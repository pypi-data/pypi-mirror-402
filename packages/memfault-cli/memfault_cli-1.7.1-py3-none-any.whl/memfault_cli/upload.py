import abc
import hashlib
import logging
import mimetypes
import os
import re
import urllib.parse
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from typing import IO, Dict, Iterable, Optional, Sequence, Tuple, Type, Union, cast
from zipfile import is_zipfile

import click
import requests
from elftools.elf.elffile import ELFFile
from mflt_build_id import BuildIdInspectorAndPatcher
from requests import HTTPError, Response, Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # pyright: ignore[reportMissingModuleSource]
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper

from .authenticator import (
    Authenticator,
    BasicAuthenticator,
    OrgTokenAuthenticator,
    ProjectKeyAuthenticator,
)
from .context import DeltaReleaseVersion, FullReleaseVersion, MemfaultCliClickContext, PackageInfo
from .elf import elf_has_debug_info, get_gnu_build_id, is_elf
from .functools_ext import cached_property

log = logging.getLogger(__name__)

GNU_BUILD_ID_RE = re.compile(r"Build ID: (?P<gnu_build_id>[a-f\d]+)")

UPLOAD_IS_TOO_BIG_RESPONSE = "Uploaded file is too big"


class UploadedAlreadyExistsError(Exception):
    pass


class UploadIsTooLargeError(Exception):
    pass


class TooManyRequestsError(Exception):
    pass


class MemfaultAPIErrorResponse:
    kind: str
    message: str

    def __init__(self, response: Response):
        self.message = response.json()["error"]["message"]
        self.kind = response.json()["error"]["type"]


def hash_io_hexdigest(name, data: IO, chunksize=2**20) -> str:
    """
    A wrapper around hashlib.new() and hexdigest() which reads
    from a stream in chunks
    """
    assert data.readable()

    # In case it's a large file, read it in chunks.
    h = hashlib.new(name)
    while True:
        chunk = data.read(chunksize)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def check_response(response: Response):
    if response.status_code >= 400:
        raise HTTPError(
            f"Request failed with HTTP status {response.status_code}\n"
            f"Response body:\n{response.content.decode() if response.content else '(empty)'}"
        )


def url_quote(value: str) -> str:
    return urllib.parse.quote(value, safe="", encoding="utf-8")


class Uploader(abc.ABC):
    authenticator_types: Sequence[Type[Authenticator]]

    def __init__(
        self,
        *,
        ctx: MemfaultCliClickContext,
        file_path: Union[str, os.PathLike],  # noqa: TID251
        authenticator: Authenticator,
        session: Union[Session, None] = None,
        **kwargs,
    ):
        self.ctx: MemfaultCliClickContext = ctx
        self.file_path = file_path
        self.authenticator: Authenticator = authenticator
        self.session = session or self._create_requests_session()

    @staticmethod
    def _create_requests_session() -> Session:
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,  # Sleep for 2s, 4s, 8s, 16s, 32s, Stop
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @property
    def base_url(self):
        return self.ctx.file_url

    @property
    def app_url(self):
        return self.ctx.app_url

    def _api_base_url(self) -> str:
        return f"{self.base_url}/api/v0"

    def _projects_base_url(self, *, base_url_override=None) -> str:
        base_url = base_url_override if base_url_override is not None else self.base_url
        return f"{base_url}/api/v0/organizations/{self.ctx.org}/projects/{self.ctx.project}"

    def _projects_ui_base_url(self) -> str:
        return f"{self.app_url}/organizations/{self.ctx.org}/projects/{self.ctx.project}"

    def upload_url(self) -> str:
        """
        The upload URL for a 'prepared upload' for the configured authentication method.
        """
        if self.authenticator.project_key_auth():
            return f"{self._api_base_url()}/upload"
        else:
            return f"{self._projects_base_url()}/upload"

    @abstractmethod
    def can_upload_file(self) -> bool:
        """Test the file pointed to by `file_path`."""

    @abstractmethod
    def entity_url(self) -> str:
        """The final URL to POST to during the prepared upload sequence."""

    def ui_url(self) -> Optional[str]:
        """The UI URL at which results from the operation can be seen"""
        return None

    def _is_already_uploaded(self) -> bool:
        return False

    def _prepare_upload(self) -> Tuple[str, str]:
        response = self.session.post(self.upload_url(), **self.authenticator.requests_auth_params())
        check_response(response)
        data = response.json()["data"]
        return data["upload_url"], data["token"]

    def _put_file(self, upload_url: str, *, progressbar=True) -> None:
        file_size = os.stat(self.file_path).st_size
        with open(self.file_path, "rb") as file, tqdm(
            total=file_size,
            desc=os.path.basename(file.name),
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            disable=not progressbar,
        ) as t:
            wrapped_file = cast("IO", CallbackIOWrapper(t.update, file, "read"))
            content_type, _ = mimetypes.guess_type(self.file_basename)
            response = self.session.put(
                upload_url,
                data=wrapped_file,
                headers={"Content-Type": content_type or "application/octet-stream"},
            )
            check_response(response)

    def post_token_extra_request_data(self) -> Optional[Dict]:
        return None

    def _post_token(self, token: str) -> None:
        json_d = {
            "file": {"token": token, "md5": self.file_md5, "name": self.file_basename},
        }
        extra_request_data = self.post_token_extra_request_data()
        if extra_request_data:
            json_d.update(extra_request_data)

        response = self.session.post(
            self.entity_url(), json=json_d, **self.authenticator.requests_auth_params()
        )

        # This file had already uploaded (maybe concurrently). Gracefully ignore the error then.
        if response.status_code == 409:
            log.info("%s: was already uploaded.", self.file_path)
            raise UploadedAlreadyExistsError(f"{self.file_path}: was already uploaded.")

        if response.status_code == 400:
            error = MemfaultAPIErrorResponse(response)
            if UPLOAD_IS_TOO_BIG_RESPONSE in error.message:
                # Need to grab the max file size from the error response, so we have to print the real message
                raise UploadIsTooLargeError(error.message + f" ({self.file_path!r})")

        if response.status_code == 429:
            raise TooManyRequestsError("Too many requests")

        check_response(response)

    @property
    def qcomm_project(self):
        response = self.session.get(
            self._projects_base_url(base_url_override=self.ctx.api_url),
            **self.authenticator.requests_auth_params(),
        )
        check_response(response)
        return response.json()["data"].get("qcomm_enabled", False)

    def upload(self, *, progressbar=True) -> bool:
        if self.ctx.check_uploaded and self._is_already_uploaded():
            log.info("%s: skipping, already uploaded.", self.file_path)
            return True
        upload_url, token = self._prepare_upload()
        self._put_file(upload_url, progressbar=progressbar)
        try:
            self._post_token(token)
            log.info("%s: uploaded!", self.file_path)
        except UploadIsTooLargeError as e:
            log.warning(str(e))
            return False
        except UploadedAlreadyExistsError:
            pass
        except TooManyRequestsError as e:
            log.warning(str(e))
            log.info(
                "Rate limit exceeded, you can enable server side developer mode to temporarily remove this limit "
                "for testing or development by accessing this URL: "
                "%s/organizations/%s/projects/%s/devices/%s?tab=developer-mode",
                self.app_url,
                self.ctx.org,
                self.ctx.project,
                self.ctx.device_serial,
            )
            return False

        if self.ui_url():
            click.echo(f"You can view in the UI here:\n   {self.ui_url()}")
        return True

    @cached_property
    def file_md5(self):
        with open(self.file_path, "rb") as f:
            return hash_io_hexdigest("md5", f)

    @property
    def file_basename(self):
        return os.path.basename(self.file_path)


def raise_on_upload_failed(uploader: Uploader) -> None:
    if not uploader.can_upload_file():
        raise click.exceptions.UsageError("Upload failed!")

    did_upload = uploader.upload()
    if not did_upload:
        raise click.exceptions.ClickException("File(s) did not successfully upload")


class BugreportUploader(Uploader):
    authenticator_types = (
        ProjectKeyAuthenticator,
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        if not is_zipfile(self.file_path):
            log.error("%s is not a valid zip file!", self.file_path)
            return False
        return True

    def entity_url(self) -> str:
        if self.authenticator.project_key_auth():
            return f"{self._api_base_url()}/upload/bugreport"
        else:
            return f"{self._projects_base_url()}/bugreports"


class CoredumpUploader(Uploader):
    authenticator_types = (
        ProjectKeyAuthenticator,
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        with open(self.file_path, "rb") as f:
            hdr = f.read(4).decode("ascii", errors="ignore")
            if hdr != "CORE":
                log.error("%s is not a Memfault Coredump", self.file_path)
                return False

        return True

    def entity_url(self) -> str:
        if self.authenticator.project_key_auth():
            return f"{self._api_base_url()}/upload/coredump"
        else:
            return f"{self._projects_base_url()}/coredumps"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        if self.ctx.core_info:
            return {
                "device_serial": self.ctx.core_info.device_serial,
            }
        return None


class ElfCoredumpUploader(Uploader):
    authenticator_types = (
        ProjectKeyAuthenticator,
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        with open(self.file_path, "rb") as f:
            elffile = ELFFile(f)
            if elffile.header["e_type"] == "ET_CORE":
                return True
        return False

    def entity_url(self) -> str:
        if self.authenticator.project_key_auth():
            return f"{self._api_base_url()}/upload/elf_coredump"
        else:
            return f"{self._projects_base_url()}/elf_coredumps"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        return {
            "device": {
                "device_serial": self.ctx.device_traits_info.device_serial,
                "hardware_version": self.ctx.device_traits_info.hardware_version,
                "software_type": self.ctx.device_traits_info.software_type,
                "software_version": self.ctx.device_traits_info.software_version,
            }
        }


class XedUploader(Uploader):
    authenticator_types = (
        ProjectKeyAuthenticator,
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        return True

    def entity_url(self) -> str:
        if self.authenticator.project_key_auth():
            return f"{self._api_base_url()}/upload/qc/x"
        else:
            return f"{self._projects_base_url()}/qc/x"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        info = self.ctx.xed_info
        return {
            "device_serial": info.device_serial,
            "hardware_version": info.hardware_version,
            "trace_attributes": [
                {"string_key": a.string_key, "value": a.value} for a in self.ctx.attributes
            ],
        }


class MarUploader(Uploader):
    authenticator_types = (
        ProjectKeyAuthenticator,
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        if not is_zipfile(self.file_path):
            log.error("%s is not a valid zip file!", self.file_path)
            return False
        return True

    def entity_url(self) -> str:
        if self.authenticator.project_key_auth():
            return f"{self._api_base_url()}/upload/mar"
        else:
            return f"{self._projects_base_url()}/mar"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        info = self.ctx.device_traits_info
        return {
            "device_serial": info.device_serial,
            "hardware_version": info.hardware_version,
            "software_type": info.software_type,
            "software_version": info.software_version,
        }


class CustomDataRecordingUploader(Uploader):
    authenticator_types = (
        ProjectKeyAuthenticator,
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        return True

    def entity_url(self) -> str:
        if self.authenticator.project_key_auth():
            return f"{self._api_base_url()}/upload/custom-data-recording"
        else:
            return f"{self._projects_base_url()}/custom-data-recording"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        device_traits = self.ctx.device_traits_info
        info = self.ctx.custom_data_recording_info
        return {
            "start_time": info.start_time.isoformat(),
            "duration_secs": int(info.duration.total_seconds()),
            "mimetypes": info.mimetypes,
            "reason": info.reason,
            "device": {
                "device_serial": device_traits.device_serial,
                "hardware_version": device_traits.hardware_version,
                "software_type": device_traits.software_type,
                "software_version": device_traits.software_version,
            },
        }


class ElfSymbolUploader(Uploader):
    authenticator_types = (
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    gnu_build_id: Optional[str] = ""

    def can_upload_file(self) -> bool:
        if os.path.islink(self.file_path) and not os.path.exists(self.file_path):
            return False

        with open(self.file_path, "rb") as f:
            if not is_elf(f):
                log.info("%s: Not an ELF file", self.file_path)
                return False

            elf = ELFFile(f)
            gnu_build_id, has_debug_info = get_gnu_build_id(elf), elf_has_debug_info(elf)
            if not gnu_build_id:
                log.info(
                    "%s: looks like an ELF but does not contain a GNU Build ID", self.file_path
                )
                return False

        self.gnu_build_id = gnu_build_id
        if not has_debug_info:
            if self.ctx.obj.get("allow_no_debug_info", False):
                log.info(
                    "%s: ELF file without .debug_info and GNU Build ID: %s",
                    self.file_path,
                    self.gnu_build_id,
                )
                return True
            else:
                log.info("%s: looks like an ELF but it has no .debug_info", self.file_path)
                return False

        log.info(
            "%s: ELF file with .debug_info and GNU Build ID: %s", self.file_path, self.gnu_build_id
        )
        return True

    def _is_already_uploaded(self) -> bool:
        if not self.gnu_build_id:
            return False
        response = self.session.head(
            f"{self._projects_base_url()}/symbols-by-gnu-build-id/{self.gnu_build_id}",
            **self.authenticator.requests_auth_params(),
        )
        try:
            check_response(response)
        except Exception:
            if response.status_code == 404:
                return False
            raise
        return True

    def entity_url(self) -> str:
        return f"{self._projects_base_url()}/symbols"


class McuSdkElfSymbolUploader(ElfSymbolUploader, Uploader):
    authenticator_types = (
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        with open(self.file_path, "rb") as file:
            if file.read(4) != b"\x7fELF":
                log.info("%s: Not an ELF file", self.file_path)
                return False
            file.seek(0)

            inspector = BuildIdInspectorAndPatcher(file)
            if not elf_has_debug_info(inspector.elf):
                log.info("%s: looks like an ELF but it has no .debug_info", self.file_path)
                return False

            _, self.gnu_build_id, _ = inspector.get_build_info()

            # NB: QC symbol files have different arg requirements depending on the subsystem the
            # ELF is associated with so we offload to the Memfault backend.
            if not self.ctx.software_info and self.gnu_build_id is None and not self.qcomm_project:
                log.error(
                    "%s: Build Id missing. Specify --software-version and --software-type options "
                    "or add a Build Id (see https://mflt.io/symbol-file-build-ids)",
                    self.file_path,
                )
                return False

        log.info("%s: ELF file with .debug_info. Build Id: %s", self.file_path, self.gnu_build_id)
        return True

    def entity_url(self) -> str:
        return f"{self._projects_base_url()}/symbols"

    def ui_url(self) -> Optional[str]:
        if not self.ctx.software_info or (
            # Unreachable with our CLI, but for safety:
            isinstance(self.ctx.software_info.version, DeltaReleaseVersion)
        ):
            return None

        software_type = url_quote(self.ctx.software_info.software_type)
        software_version = url_quote(self.ctx.software_info.version.software_version)
        return (
            f"{self._projects_ui_base_url()}/software/{software_type}/versions/{software_version}"
        )

    def post_token_extra_request_data(self) -> Optional[Dict]:
        if not self.ctx.software_info:
            return None

        info = self.ctx.software_info
        return {
            "software_version": {
                "version": info.version.to_json_representable(),
                "software_type": info.software_type,
                **({"revision": info.revision} if info.revision else {}),
            },
        }


class ReleaseArtifactUploader(Uploader):
    authenticator_types = (
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        # There are no restrictions for the type of binary a customer uses for
        # a release
        return True

    def _is_already_uploaded(self) -> bool:
        return False

    def entity_url(self) -> str:
        return f"{self._projects_base_url()}/releases/ota_payload"

    def ui_url(self) -> str:
        info = self.ctx.software_info
        releases_url = f"{self._projects_ui_base_url()}/releases"
        delta_releases_url = f"{self._projects_ui_base_url()}/delta-releases"

        if not info:
            return releases_url

        if info.software_type == "android-build":
            # In case of Android, the created Release.version may not be the same
            # as the SoftwareVersion.version, in case build fingerprints are used,
            # the Release.version will be "stripped" (i.e. */*/*:*/*/*:*/*::1.0.0):
            return (
                delta_releases_url
                if isinstance(info.version, DeltaReleaseVersion)
                else releases_url
            )

        if isinstance(info.version, DeltaReleaseVersion):
            from_version = url_quote(info.version.delta_from)
            to_version = url_quote(info.version.delta_to)
            return f"{delta_releases_url}/{from_version}/{to_version}"

        return f"{releases_url}/{url_quote(info.version.software_version)}"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        info = self.ctx.software_info
        assert info

        return {
            "software_version": {
                "version": info.version.to_json_representable(),
                "software_type": info.software_type,
                **({"revision": info.revision} if info.revision else {}),
            },
            "must_pass_through": self.ctx.must_pass_through,
            "hardware_version": self.ctx.hardware_version,
            "notes": self.ctx.notes,
            **({"extra_info": self.ctx.extra_info} if self.ctx.extra_info else {}),
        }


def walk_files(toplevel: str) -> Iterable[str]:
    for root, _dirs, files in os.walk(toplevel):
        for file in files:
            yield os.path.join(root, file)


class ParallelUploader(Uploader):
    uploader_cls: Type[Uploader]

    def __init__(
        self,
        *args,
        file_paths: Iterable[Union[str, os.PathLike]],  # noqa: TID251
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.file_paths = file_paths

    def can_upload_file(self) -> bool:
        # TODO: refactor file_path/file_paths
        # self.file_path is unused and replaced by self.file_paths
        return True

    def upload(self, *, progressbar=True) -> bool:
        queued_uploaders = []
        did_upload = False

        with Uploader._create_requests_session() as session:
            for file_path in self.file_paths:
                uploader = self.uploader_cls(
                    ctx=self.ctx,
                    file_path=file_path,
                    authenticator=self.authenticator,
                    session=session,
                )
                if uploader.can_upload_file():
                    queued_uploaders.append(uploader)
                    did_upload |= True
                else:
                    log.info("%s: skipping...", file_path)

            def do_upload(uploader: Uploader):
                uploader.upload(progressbar=False)

            # If we find that we have more implementations that need to do parallel uploads,
            # We should generalize this logic into a class or have a function called `get_uploaders`
            # that the calling client can then parallelize by calling `.upload()` on each.
            with ThreadPoolExecutor(max_workers=self.ctx.concurrency) as pool:
                # NB: We need to read the result for exceptions to be raised
                for result in pool.map(do_upload, queued_uploaders):
                    del result

            return did_upload

    def entity_url(self) -> str:
        raise NotImplementedError


class ElfSymbolDirectoryUploader(ParallelUploader):
    uploader_cls = ElfSymbolUploader
    authenticator_types = (
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )


class ProguardMappingUploader(Uploader):
    authenticator_types = (
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def __init__(
        self,
        *,
        ctx: MemfaultCliClickContext,
        file_path: str,
        authenticator: Authenticator,
        package_info: PackageInfo,
        **kwargs,
    ):
        super().__init__(ctx=ctx, file_path=file_path, authenticator=authenticator, **kwargs)
        self.package_info = package_info

    def can_upload_file(self) -> bool:
        return True

    def entity_url(self) -> str:
        return f"{self._projects_base_url()}/symbols"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        return {
            "software_version": {
                "version": f"{self.package_info.version_name}:{self.package_info.version_code}",
                "software_type": self.package_info.name,
            },
        }


class AndroidAppSymbolsUploader(Uploader):
    authenticator_types = (
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        if not os.path.isdir(self.file_path):
            log.error(
                '%s is not a directory. Please specify the Android app\'s root "build" path instead!',
                self.file_path,
            )
            return False
        return True

    def _find_apk_path(self) -> str:
        apk_dir = self.ctx.android_apk_dir
        if apk_dir is None:
            apk_dir = os.path.join(self.file_path, "outputs", "apk", self.ctx.build_variant)
        if not os.path.isdir(apk_dir):
            raise click.exceptions.FileError(
                apk_dir, hint='Please pass the Android app\'s root "build" path!'
            )
        apk_glob = os.path.join(apk_dir, "*.apk")
        apks = glob(apk_glob)
        if not apks:
            raise click.exceptions.FileError(apk_glob, hint="No .apk found!")
        if len(apks) > 1:
            raise click.exceptions.FileError(apk_glob, hint="Multiple .apks found!")
        return apks[0]

    def _get_package_info_from_apk(self) -> PackageInfo:
        from pyaxmlparser import APK

        apk = APK(self._find_apk_path())
        name = apk.get_package()
        assert name
        return PackageInfo(name, apk.version_name, apk.version_code)

    def _find_mapping_txt(self) -> Optional[str]:
        if self.ctx.android_mapping_txt:
            return self.ctx.android_mapping_txt
        # In older version, the default folder was called "proguard", later it got renamed to "mapping":
        subdirs = ("mapping", "proguard")
        paths_to_check = tuple(
            os.path.join(
                self.file_path, "outputs", "mapping", self.ctx.build_variant, "mapping.txt"
            )
            for _ in subdirs
        )
        for path in paths_to_check:
            if os.path.isfile(path):
                return path
        log.info("No mapping.txt found in default locations, assuming ProGuard/R8 is disabled...")
        return None

    def _upload_mapping_txt(self) -> bool:
        mapping_txt_path = self._find_mapping_txt()
        if not mapping_txt_path:
            return False
        package_info = self.ctx.android_package_info
        if not package_info:
            package_info = self._get_package_info_from_apk()
        pg_uploader = ProguardMappingUploader(
            ctx=self.ctx,
            file_path=mapping_txt_path,
            package_info=package_info,
            authenticator=self.authenticator,
        )
        return pg_uploader.upload()

    def _upload_ndk_symbols(self) -> bool:
        native_libs_dir = self.ctx.android_native_libs_dir
        if native_libs_dir is None:
            native_libs_dir = os.path.join(
                self.file_path, "intermediates", "cmake", self.ctx.build_variant
            )
        if not os.path.isdir(native_libs_dir):
            log.info("No native libs found in %s, assuming none were built...", native_libs_dir)
            return False
        native_libs_dir = str(native_libs_dir)
        sym_dir_uploader = ElfSymbolDirectoryUploader(
            ctx=self.ctx,
            file_path=native_libs_dir,
            authenticator=self.authenticator,
            file_paths=walk_files(native_libs_dir),
        )
        return sym_dir_uploader.upload()

    def upload(self, *, progressbar=True) -> bool:
        did_upload = self._upload_mapping_txt() or self._upload_ndk_symbols()
        if not did_upload:
            raise click.exceptions.UsageError("No files uploaded!")
        return did_upload

    def entity_url(self) -> str:
        raise NotImplementedError


class SoftwareVersionSBOMUploader(Uploader):
    authenticator_types = (
        OrgTokenAuthenticator,
        BasicAuthenticator,
    )

    def can_upload_file(self) -> bool:
        # let the server decide
        return True

    def _is_already_uploaded(self) -> bool:
        return False

    def entity_url(self) -> str:
        return f"{self._projects_base_url()}/sboms"

    def ui_url(self) -> str:
        info = self.ctx.software_info
        assert info
        return f"{self._projects_ui_base_url()}/software/{info.software_type}/versions"

    def post_token_extra_request_data(self) -> Optional[Dict]:
        info = self.ctx.software_info
        assert info
        assert isinstance(info.version, FullReleaseVersion)
        return {
            "software_version": info.version.to_json_representable(),
            "software_type": info.software_type,
        }

    def upload(self, *, progressbar: bool = True) -> bool:
        return super().upload(progressbar=progressbar)
