import dataclasses
import logging
import pathlib
import platform
import re
import secrets
import subprocess
import tarfile
import tempfile
from enum import Enum
from typing import Iterable, List, Optional

import click

from memfault_cli.authenticator import BasicAuthenticator, OrgTokenAuthenticator
from memfault_cli.context import MemfaultCliClickContext
from memfault_cli.upload import ElfSymbolDirectoryUploader

from .elf import ELFFileInfo, find_elf_files
from .upload import raise_on_upload_failed

# See https://docs.yoctoproject.org/overview-manual/concepts.html#package-splitting
# for the directory structure of the Yocto build output.

log = logging.getLogger(__name__)


def find_elf_files_from_image(image_tar: pathlib.Path) -> Iterable[ELFFileInfo]:
    with tarfile.open(
        image_tar, "r:*"
    ) as tar, tempfile.TemporaryDirectory() as extraction_path_str:
        tar.extractall(extraction_path_str)  # noqa: S202
        subprocess.check_call(["chmod", "-R", "u+r", extraction_path_str])
        extraction_path = pathlib.Path(extraction_path_str)
        yield from find_elf_files(extraction_path, relative_to=extraction_path)


# https://docs.yoctoproject.org/ref-manual/variables.html?highlight=package_debug_split_style#term-PACKAGE_DEBUG_SPLIT_STYLE
class PackageDebugSplitStyle(Enum):
    DEBUG = ".debug"
    DEBUG_WITH_SRCPKG = "debug-with-srcpkg"
    DEBUG_WITHOUT_SRC = "debug-without-src"
    DEBUG_FILE_DIRECTORY = "debug-file-directory"


# https://docs.yoctoproject.org/ref-manual/variables.html?highlight=package_debug_split_style#term-PACKAGE_DEBUG_SPLIT_STYLE
def guess_debug_file_path(bin_path: pathlib.Path, style: PackageDebugSplitStyle) -> pathlib.Path:
    if style == PackageDebugSplitStyle.DEBUG_FILE_DIRECTORY:
        debug_file_directory = pathlib.Path("/usr/lib/debug")
        return debug_file_directory / bin_path.relative_to(debug_file_directory)

    return bin_path.parent / ".debug" / bin_path.name


def eu_unstrip_path_from_components_dir(components_dir: pathlib.Path) -> pathlib.Path:
    eu_unstrip_sysroot_path = pathlib.Path("usr", "bin", "eu-unstrip")
    return components_dir / platform.machine() / "elfutils-native" / eu_unstrip_sysroot_path


def eu_unstrip_run(
    *,
    stripped_elf: pathlib.Path,
    debug_elf: pathlib.Path,
    output_dir: pathlib.Path,
    eu_unstrip_path: pathlib.Path,
) -> Optional[pathlib.Path]:
    random = secrets.token_urlsafe(4)
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / f"{stripped_elf.name}-{random}"

    pipe = subprocess.run(
        (eu_unstrip_path, "--output", output_path, stripped_elf, debug_elf),
        stderr=subprocess.PIPE,
        check=False,
    )

    if pipe.stderr:
        log.debug("Unexpected stderr from eu-unstrip: %s", pipe.stderr)
        return None

    return output_path


class OeInitBuildEnvNotSourcedError(Exception):
    pass


def get_from_bitbake_build_env(variables: List[str]) -> List[Optional[str]]:
    grep_pattern = "|".join(f"^{variable}" for variable in variables)

    try:
        bitbake_environment_process = subprocess.Popen(
            ("bitbake", "--environment"), stdout=subprocess.PIPE
        )
        output = subprocess.check_output(
            ("grep", "-E", grep_pattern), stdin=bitbake_environment_process.stdout
        )
        bitbake_environment_process.wait()
        output_str = output.decode()
    except subprocess.CalledProcessError as err:
        raise OeInitBuildEnvNotSourcedError(
            "Failed to run 'bitbake -e | grep'. Have you run 'source oe-init-build-env'?"
        ) from err

    values: List[Optional[str]] = []

    for variable in variables:
        matcher = r"(^|\n)" + re.escape(variable) + '="(?P<value>.*)"($|\n)'
        matches = re.search(matcher, output_str)
        if matches:
            value = matches.group("value")
            values.append(value or None)
        else:
            values.append(None)

    return values


@dataclasses.dataclass(frozen=True)
class BitbakeBuildEnvResult:
    eu_unstrip_path: pathlib.Path
    package_debug_split_style: PackageDebugSplitStyle


def get_necessary_from_bitbake_build_env() -> BitbakeBuildEnvResult:
    components_dir: Optional[str] = None
    package_debug_split_style: Optional[str] = None

    click.echo("Fetching configuration from bitbake build environment...")
    components_dir, package_debug_split_style = get_from_bitbake_build_env([
        "COMPONENTS_DIR",
        "PACKAGE_DEBUG_SPLIT_STYLE",
    ])

    components_dir_path = pathlib.Path(components_dir) if components_dir else None
    if not components_dir_path or not components_dir_path.exists():
        raise click.exceptions.FileError(
            "Failed to get a valid COMPONENTS_DIR path from bitbake --environment"
            f" (components_dir={components_dir})"
        )

    eu_unstrip_path = eu_unstrip_path_from_components_dir(components_dir_path)
    if not eu_unstrip_path.exists():
        raise click.exceptions.FileError(
            f"Failed to find executable eu-unstrip in expected location {eu_unstrip_path}"
        )

    try:
        style = PackageDebugSplitStyle(package_debug_split_style)
    except ValueError as err:
        raise click.exceptions.UsageError(
            "Unsupported or missing PACKAGE_DEBUG_SPLIT_STYLE from bitbake --environment"
            f" (package_debug_split_style={package_debug_split_style})"
        ) from err

    return BitbakeBuildEnvResult(eu_unstrip_path=eu_unstrip_path, package_debug_split_style=style)


def upload_linux_elf_symbols(ctx: MemfaultCliClickContext, archive: pathlib.Path) -> None:
    with tempfile.TemporaryDirectory() as extraction_path_str, tarfile.open(
        archive, "r:*"
    ) as archive_tar:
        upload_paths = []

        extraction_path = pathlib.Path(extraction_path_str)
        archive_tar.extractall(extraction_path)  # noqa: S202
        subprocess.check_call(["chmod", "-R", "u+r", extraction_path])

        for elf_info in find_elf_files(extraction_path, relative_to=extraction_path):
            if "/lib/modules" in str(elf_info.path):
                # Not interested in kernel modules and we don't have debug
                # symbols for those anyway.
                continue
            upload_paths.append(elf_info.path)

        raise_on_upload_failed(
            ElfSymbolDirectoryUploader(
                ctx=ctx,
                file_path=archive,  # Not used. TODO: refactor!
                authenticator=ctx.create_authenticator(OrgTokenAuthenticator, BasicAuthenticator),
                file_paths=upload_paths,
            )
        )


def process_and_upload_yocto_symbols(
    ctx: MemfaultCliClickContext,
    image: pathlib.Path,
    dbg_image: pathlib.Path,
    *,
    build_env: BitbakeBuildEnvResult,
) -> None:
    def _image_elfs(image_tar: pathlib.Path) -> Iterable[ELFFileInfo]:
        with click.progressbar(
            find_elf_files_from_image(image_tar),
            label="Processing binaries in image...",
        ) as bar:
            yield from bar

    dbg_image_size_mb = f"{dbg_image.stat().st_size / 10e5:.2f}"

    with tempfile.TemporaryDirectory() as workbench_dir_str, tarfile.open(
        dbg_image, "r:*"
    ) as debug_image_tar:
        workbench_dir = pathlib.Path(workbench_dir_str)
        upload_paths: List[pathlib.Path] = []
        missing_infos: List[ELFFileInfo] = []

        debug_symbols_dir = workbench_dir / "debug"
        debug_symbols_dir.mkdir()

        click.echo(f"Extracting debug symbols ({dbg_image_size_mb} MB) to a temporary directory...")
        debug_image_tar.extractall(debug_symbols_dir)  # noqa: S202
        subprocess.check_call(["chmod", "-R", "u+r", debug_symbols_dir])

        for elf_info in _image_elfs(image):
            if "/lib/modules" in str(elf_info.path):
                # Not interested in kernel modules and we don't have debug
                # symbols for those anyway.
                continue

            debug_elf_path = guess_debug_file_path(
                elf_info.relpath, style=build_env.package_debug_split_style
            )
            upload_path = eu_unstrip_run(
                stripped_elf=elf_info.path,
                debug_elf=debug_symbols_dir / debug_elf_path,
                output_dir=workbench_dir / "unstripped",
                eu_unstrip_path=build_env.eu_unstrip_path,
            )
            if upload_path:
                upload_paths.append(upload_path)
            else:
                missing_infos.append(elf_info)

        ElfSymbolDirectoryUploader(
            ctx=ctx,
            file_path=image,  # Not used. TODO: refactor!
            authenticator=ctx.create_authenticator(OrgTokenAuthenticator, BasicAuthenticator),
            file_paths=upload_paths,
        ).upload()

        for info in missing_infos:
            log.warning(
                "Could not find debug info for %s (GNU build ID %s)",
                info.relpath,
                info.gnu_build_id,
            )
