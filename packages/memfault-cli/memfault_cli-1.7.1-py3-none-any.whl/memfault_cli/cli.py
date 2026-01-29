import http.client
import logging
import os
import pathlib
from base64 import b64decode
from datetime import datetime, timezone
from typing import List, Optional, Type

import click

from ._version import version
from .authenticator import BasicAuthenticator, OrgTokenAuthenticator, ProjectKeyAuthenticator
from .chunk import MemfaultChunk
from .console import MemfaultMiniterm
from .context import MemfaultCliClickContext
from .deploy import Deployer
from .linux import (
    BitbakeBuildEnvResult,
    PackageDebugSplitStyle,
    get_necessary_from_bitbake_build_env,
    process_and_upload_yocto_symbols,
    upload_linux_elf_symbols,
)
from .upload import (
    AndroidAppSymbolsUploader,
    BugreportUploader,
    CoredumpUploader,
    CustomDataRecordingUploader,
    ElfCoredumpUploader,
    ElfSymbolDirectoryUploader,
    ElfSymbolUploader,
    MarUploader,
    McuSdkElfSymbolUploader,
    ReleaseArtifactUploader,
    SoftwareVersionSBOMUploader,
    Uploader,
    XedUploader,
    raise_on_upload_failed,
    walk_files,
)

log = logging.getLogger(__name__)


pass_memfault_cli_context = click.make_pass_decorator(MemfaultCliClickContext, ensure=True)
click_argument_path = click.argument("path", type=click.Path(exists=True))
click_option_concurrency = click.option(
    "--concurrency",
    required=False,
    default=8,
    type=int,
    help="Max number of concurrent web requests",
)
click_option_revision = click.option(
    "--revision", help="Revision SHA or # (git, SVN, etc.)", required=False
)


@click.group()
@click.option("--email", help="Account email to authenticate with")
@click.password_option(
    "--password", prompt=False, help="Account password or user API key to authenticate with"
)
@click.option("--project-key", help="Memfault Project Key")
@click.option("--org-token", help="Organization Auth Token")
@click.option("--org", help="Organization slug", callback=MemfaultCliClickContext.validate_slug_arg)
@click.option("--project", help="Project slug", callback=MemfaultCliClickContext.validate_slug_arg)
@click.option("--url", hidden=True)
@click.option("--verbose", help="Log verbosely", is_flag=True)
@click.version_option(version=version)
@pass_memfault_cli_context
def cli(ctx: MemfaultCliClickContext, **kwargs):
    ctx.obj.update(kwargs)

    if ctx.verbose:
        click.echo(f"version: {version}")

        logging.basicConfig(level=logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        httpclient_logger = logging.getLogger("http.client")
        httpclient_logger.setLevel(logging.DEBUG)

        httpclient_logger = logging.getLogger("memfault_cli")
        httpclient_logger.setLevel(logging.DEBUG)

        def httpclient_log(*args) -> None:
            httpclient_logger.log(logging.DEBUG, " ".join(args))

        http.client.print = httpclient_log  # pyright: ignore[reportAttributeAccessIssue]
        http.client.HTTPConnection.debuglevel = 1


def _do_upload_or_raise(
    ctx: MemfaultCliClickContext, path: str, uploader_cls: Type[Uploader], **kwargs
) -> None:
    authenticator = ctx.create_authenticator(*uploader_cls.authenticator_types)
    uploader = uploader_cls(ctx=ctx, file_path=path, authenticator=authenticator, **kwargs)
    raise_on_upload_failed(uploader)


@cli.command(name="upload-coredump")
@click.option(
    "--device-serial",
    required=False,
    help="A fallback unique identifier of a device, when one is not present in the coredump",
)
@click_argument_path
@pass_memfault_cli_context
def upload_coredump(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload an MCU coredump for analysis.

    Coredumps can be added to an MCU platform by integrating the Memfault C SDK:
    https://github.com/memfault/memfault-firmware-sdk
    """
    ctx.obj.update(**kwargs)

    _do_upload_or_raise(ctx, path, CoredumpUploader)


@cli.command(name="upload-xed")
@click.option(
    "--hardware-version",
    required=True,
    help="Required for MCU builds, see https://mflt.io/34PyNGQ",
)
@click.option(
    "--device-serial",
    required=True,
    help="The unique identifier of a device",
)
@click.option(
    "--attribute",
    type=click.Tuple([str, str]),
    multiple=True,
    help="""
    Attribute associated with the uploaded file. Multiple attributes can be passed.
    The value argument is attempted to be interpreted as a JSON string first, if that
    fails, the value is interpreted as a string value as-is. Note however that only
    number, boolean, string or null values are allowed (objects and arrays are not allowed).

    Examples:

    Key "my_int" with numeric value 1234:

    --attribute my_int 1234

    Key "my_string" with string value 'hello':

    --attribute my_string hello

    Key "my_bool" with boolean true value:

    --attribute my_bool true
    """,
)
@click_argument_path
@pass_memfault_cli_context
def upload_xed(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload an .xed or .xcd file for analysis."""
    ctx.obj.update(**kwargs)

    _do_upload_or_raise(ctx, path, XedUploader)


@cli.command(name="upload-bugreport")
@click_argument_path
@pass_memfault_cli_context
def upload_bugreport(ctx: MemfaultCliClickContext, path: str):
    """Upload an Android Bug Report for analysis by Memfault."""
    uploader_cls = BugreportUploader
    _do_upload_or_raise(ctx, path, uploader_cls)


@cli.command(name="upload-symbols")
@click.option(
    "--software-type",
    required=False,
    help="Required for MCU builds, see https://mflt.io/34PyNGQ",
)
@click.option(
    "--software-version",
    required=False,
    help="Required for MCU builds, see https://mflt.io/34PyNGQ",
)
@click_option_revision
@click_option_concurrency
@click_argument_path
@pass_memfault_cli_context
def upload_symbols(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """[DEPRECATED] Upload symbols for an MCU or Android build.

    Please use upload-aosp-symbols or upload-mcu-symbols instead!
    """
    ctx.obj.update(**kwargs)

    uploader: Type[Uploader]
    if os.path.isdir(path):
        uploader = ElfSymbolDirectoryUploader
        uploader_kwargs = {"file_paths": walk_files(path)}
    elif ctx.software_info is None:
        uploader = ElfSymbolUploader
        uploader_kwargs = {}
    else:
        uploader = McuSdkElfSymbolUploader
        uploader_kwargs = {}

    _do_upload_or_raise(ctx, path, uploader, **uploader_kwargs)


@cli.command(name="upload-mar")
@click.option(
    "--hardware-version",
    required=True,
    help="Required to identify the type of Android hardware, see https://mflt.io/34PyNGQ/#android. By default the ro.product.model property is used.",
)
@click.option(
    "--software-type",
    required=True,
    help="Required to identify the Android system software, see https://mflt.io/34PyNGQ/#android-1",
)
@click.option(
    "--software-version",
    required=True,
    help="Required to identify single builds on Android devices, see https://mflt.io/34PyNGQ/#software-version",
)
@click.option(
    "--device-serial",
    required=True,
    help="The unique identifier of a device",
)
@click_argument_path
@pass_memfault_cli_context
def upload_mar(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload a Memfault Archive File (mar) file for analysis."""
    ctx.obj.update(**kwargs)
    _do_upload_or_raise(ctx, path, MarUploader)


@cli.command(name="upload-elf-coredump")
@click.option(
    "--device-serial",
    required=True,
    help="The unique identifier of a device.",
)
@click.option(
    "--hardware-version",
    required=True,
    help="""
    Required to identify the type of hardware.
    See https://mflt.io/34PyNGQ/#hardware-version
    """,
)
@click.option(
    "--software-type",
    required=True,
    help="""
    Required to identify the type of the software that generated the coredump.
    See https://mflt.io/34PyNGQ/#software-type
    """,
)
@click.option(
    "--software-version",
    required=True,
    help="""
    Required to identify single builds on Linux devices.
    See https://mflt.io/34PyNGQ/#software-version
    """,
)
@click_argument_path
@pass_memfault_cli_context
def upload_elf_coredump(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload a Linux ELF coredump for analysis by Memfault."""

    ctx.obj.update(**kwargs)

    _do_upload_or_raise(ctx, path, ElfCoredumpUploader)


@cli.command(name="upload-yocto-symbols")
@click.option(
    "--image",
    "-i",
    required=True,
    help="""
    The path to the root filesystem image as produced by Yocto's do_image_*.
    The file is expected to reside in the location where Yocto produced the
    file (tmp/deploy/images/${PACKAGE_ARCH}/images).

    Supported formats: .tar, .tar.bz2, .tar.gz, .tar.xz
    """,
    type=click.Path(exists=True, resolve_path=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--dbg-image",
    "-d",
    required=True,
    help="""
    The path to the dbg filesystem image as produced by Yocto's
    IMAGE_GEN_DEBUGFS option. The file is expected to reside in the location
    where Yocto produced the file (tmp/deploy/images/${PACKAGE_ARCH}/images).

    To generate it alongside the required elfutils-native, add the following to
    your main image (note that the main image will not be affected except for
    its build dependencies):

    \b
    DEPENDS:append = " elfutils-native"
    IMAGE_GEN_DEBUGFS = "2"
    IMAGE_FSTYPES_DEBUGFS = "tar.bz2"

    Supported formats: .tar, .tar.bz2, .tar.gz, .tar.xz
    """,
    type=click.Path(exists=True, resolve_path=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--eu-unstrip-path",
    required=False,
    help="""
    Path to a local eu-unstrip binary from elfutils
    (https://sourceware.org/elfutils/).

    Not necessary if running after 'source oe-init-build-env'.

    If you pass --eu-unstrip-path, you must also pass --package-debug-split-style.
    """,
    type=click.Path(exists=True, resolve_path=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--package-debug-split-style",
    type=click.Choice([style.value for style in PackageDebugSplitStyle]),
    required=False,
    help="""
    Your project's PACKAGE_DEBUG_SPLIT_STYLE. In Poky, defaults to
    'debug-with-srcpkg'.

    Not necessary if running after 'source oe-init-build-env'.

    If you pass --package-debug-split-style, you must also pass --eu-unstrip-path.
    """,
)
@click_option_concurrency
@pass_memfault_cli_context
def upload_yocto_symbols(
    ctx: MemfaultCliClickContext,
    image: pathlib.Path,
    dbg_image: pathlib.Path,
    eu_unstrip_path: Optional[pathlib.Path],
    package_debug_split_style: Optional[str],
    **kwargs,
):
    """Upload symbols for a Linux Yocto build.

    To see a full example, take a look at the Linux SDK example project:
    https://mflt.io/yocto-upload-symbols

    Example Yocto Symbol Upload:

        \b
        $ bitbake my-image
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
            upload-yocto-symbols \\
                   --image build/tmp/deploy/images/raspberrypi3/my-image-raspberrypi3.tar.bz2 \\
                   --dbg-image build/tmp/deploy/images/raspberrypi3/my-image-raspberrypi3-dbg.tar.bz2

    Note: To specify a temporary directory to use for extracting the debug symbols,
    use the TMPDIR environment variable (this command can use a significant amount
    of space while it is running). Otherwise the default temporary location will
    be used.
    """
    ctx.obj.update(**kwargs)

    if eu_unstrip_path and package_debug_split_style:
        build_env = BitbakeBuildEnvResult(
            eu_unstrip_path=eu_unstrip_path,
            package_debug_split_style=PackageDebugSplitStyle(package_debug_split_style),
        )
    elif eu_unstrip_path or package_debug_split_style:
        raise click.exceptions.UsageError(
            "Parameters '--eu-unstrip-path' and '--package-debug-split-style' must be used together."
        )
    else:
        build_env = get_necessary_from_bitbake_build_env()

    process_and_upload_yocto_symbols(ctx, image, dbg_image, build_env=build_env)


@cli.command(name="upload-elf-symbols")
@click.option(
    "--archive",
    "-a",
    required=True,
    help="""
    The path to the root filesystem image with ELF files
    built with debug symbols.

    Supported formats: .tar, .tar.bz2, .tar.gz, .tar.xz
    """,
    type=click.Path(exists=True, resolve_path=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--allow-no-debug-info",
    is_flag=True,
    help="Allow uploading ELF files even without DWARF debug info",
)
@click_option_concurrency
@pass_memfault_cli_context
def upload_elf_symbols(
    ctx: MemfaultCliClickContext,
    archive: pathlib.Path,
    **kwargs,
):
    """Upload symbols from a tarball of binaries

    Extracts the archive, finds the ELF files within it,
    and uploads them to Memfault. Memfault will use symbol files
    to process coredumps that have a matching Build ID.

    Note: To specify a temporary directory to use for extracting the debug symbols,
    use the TMPDIR environment variable (this command can use a significant amount
    of space while it is running). Otherwise, the default temporary location will
    be used.
    """
    ctx.obj.update(**kwargs)
    upload_linux_elf_symbols(ctx, archive)


@cli.command(name="upload-mcu-symbols")
@click.option(
    "--software-type",
    required=False,
    help="Required for MCU symbols without Build Id, see https://mflt.io/symbol-file-build-ids",
)
@click.option(
    "--software-version",
    required=False,
    help="Required for MCU symbols without Build Id, see https://mflt.io/symbol-file-build-ids",
)
@click.option(
    "--check-uploaded/--no-check-uploaded",
    required=False,
    default=True,
    help="Control whether to check for an existing symbol file before uploading",
)
@click_option_revision
@click_argument_path
@pass_memfault_cli_context
def upload_mcu_symbols(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload symbols for an MCU build.

    Memfault will use the Build Id in the symbol file to identify it and match
    it with data sent by that build. See https://mflt.io/symbol-file-build-ids
    for more information on enabling Build Id in your project.

    In case a Build Id cannot be found in the symbol file, a `--software-type`
    and `--software-version` must be passed. This will then be used as
    identifying information instead of a Build Id.

    Even if a Build Id is available, it is possible to pass a `--software-type`
    and `--software-version`. This will link the symbol file with the specified
    Software Version, which can be useful to easily retrieve the symbol file by
    Software Version through the Memfault UI.

    \b
    Example MCU Symbols Upload:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
            upload-mcu-symbols \\
            build/symbols.elf

    \b
    Example MCU Symbols Upload, associating it with a Software Version:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
            upload-mcu-symbols \\
            --software-type stm32-fw \\
            --software-version 1.0.0-alpha \\
            --revision 89335ffade90ff7697e2ce5238bd4c68978b6d6e \\
            build/symbols.elf
    """
    ctx.obj.update(**kwargs)

    _do_upload_or_raise(ctx, path, McuSdkElfSymbolUploader)


@cli.command(name="upload-aosp-symbols")
@click_option_concurrency
@click_argument_path
@pass_memfault_cli_context
def upload_aosp_symbols(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload symbols for an Android OS/AOSP build.

    \b
    Example AOSP Symbol Upload:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink
            upload-aosp-symbols \\
            out/target/product/generic/symbols

        Reference: https://mflt.io/android-os-symbol-files
    """
    ctx.obj.update(**kwargs)

    uploader: Type[Uploader]
    if os.path.isdir(path):
        uploader = ElfSymbolDirectoryUploader
        uploader_kwargs = {"file_paths": walk_files(path)}
    else:
        uploader = ElfSymbolUploader
        uploader_kwargs = {}

    _do_upload_or_raise(ctx, path, uploader, **uploader_kwargs)


@cli.command(name="upload-android-app-symbols")
@click.option(
    "--build-variant",
    required=True,
    help="The build variant for which to upload the Android app symbols",
)
@click.option(
    "--package",
    required=False,
    help="The package identifier of the app. When not specified, it is read from the .apk",
)
@click.option(
    "--version-name",
    required=False,
    help="The version name of the app. When not specified, it is read from the .apk",
)
@click.option(
    "--version-code",
    required=False,
    help="The version code of the app. When not specified, it is read from the .apk",
)
@click.option(
    "--mapping-txt",
    required=False,
    help="The path to the Proguard/R8 mapping.txt file. When not specified, the gradle default locations are searched.",
)
@click.option(
    "--native-libs-dir",
    required=False,
    help="The path to the dir containing native libs. When not specified, the gradle default locations are searched.",
)
@click.option(
    "--apk-dir",
    required=False,
    help="The path to the apk. When not specified, the gradle default locations are searched.",
)
@click_option_concurrency
@click_argument_path
@pass_memfault_cli_context
def upload_android_app_symbols(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload symbols & R8/ProGuard mapping for an Android app build.

    Pass the root 'build' directory of the Android app as argument, for example:

    memfault upload-android-app-symbols --build-variant=release ~/my/app/build

    The command will automatically try to locate the mapping.txt and extract the
    version and package identifier from the .apk file.

    If this automatic behavior does not work in your use case, consider using
    option flags (i.e. --version-code, --version-name, --package, etc.) to specify
    the required information directly.
    """
    ctx.obj.update(**kwargs)
    uploader: Type[Uploader] = AndroidAppSymbolsUploader
    _do_upload_or_raise(ctx, path, uploader)


@cli.command(name="upload-ota-payload")
@click.option("--hardware-version", required=True)
@click.option("--software-type", required=True)
@click.option(
    "--software-version",
    required=False,
    help="Make the OTA Payload a Full Release payload for this version.",
)
@click.option(
    "--delta-from",
    required=False,
    help="Pass --delta-from FROM_VERSION make the OTA Payload a Delta Release payload from the version FROM_VERSION. Use alongside --delta-to TO_VERSION",
)
@click.option(
    "--delta-to",
    required=False,
    help="Pass --delta-to TO_VERSION to make the OTA Payload a Delta Release payload to version TO_VERSION. Use alongside --delta-from FROM_VERSION.",
)
@click.option("--notes", default="", help="Optional release notes.")
@click.option(
    "--must-pass-through",
    required=False,
    is_flag=True,
    help="When the Release is deployed to a Cohort, forces a device to update through this version even if a newer version has also been deployed to the Cohort.",
)
@click.option(
    "--extra-metadata",
    required=False,
    multiple=True,
    help="Extra metadata in the form of `<key>=<value>` to attach to this artifact. This metadata will be returned alongside the artifact when the release is fetched.",
)
@click_option_revision
@click_argument_path
@pass_memfault_cli_context
def upload_ota_payload(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload a binary to be used for an OTA update.

    See https://mflt.io/34PyNGQ for details about 'hardware-version',
    'software-type' and 'software-version' nomenclature.

    When deployed, this is the binary that will be returned from the Memfault /latest endpoint
    which can be used for an Over The Air (OTA) update.

    \b
    Example OTA Upload:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
            upload-ota-payload \\
            --hardware-version mp \\
            --software-type stm32-fw \\
            --software-version 1.0.0-alpha \\
            --revision 89335ffade90ff7697e2ce5238bd4c68978b6d6e \\
            build/stm32-fw.bin

    \b
    Example Delta OTA Upload:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
            upload-ota-payload \\
            --hardware-version mp \\
            --software-type stm32-fw \\
            --delta-from 0.9.0 \\
            --delta-to 1.0.0-alpha \\
            --revision 89335ffade90ff7697e2ce5238bd4c68978b6d6e \\
            build/stm32-fw-delta.bin

    Reference: https://mflt.io/create-release
    """
    ctx.obj.update(**kwargs)
    ctx.check_required_either(
        {"software_version"}, {"delta_from", "delta_to"}, mutually_exclusive=True
    )
    _do_upload_or_raise(ctx, path, ReleaseArtifactUploader)


@cli.command(name="upload-custom-data-recording")
@click.option(
    "--hardware-version",
    type=click.STRING,
    required=True,
    help="Required to identify the type of hardware.",
)
@click.option(
    "--software-type",
    type=click.STRING,
    required=True,
    help="Required to identify the system software",
)
@click.option(
    "--software-version",
    type=click.STRING,
    required=True,
    help="Required to identify single builds on Devices",
)
@click.option(
    "--device-serial",
    required=True,
    type=click.STRING,
    help="The unique identifier of a Device",
)
@click.option(
    "--start-time",
    required=False,
    default=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
    type=click.DateTime(formats=("%Y-%m-%dT%H:%M:%S%z",)),
    help="Timestamp of when the custom data recording started. The timezone needs to be specified. Defaults to the current time. Example: '2022-10-14T10:33:23Z' or '2022-10-14T10:33:23+0200'.",
)
@click.option(
    "--duration-secs",
    required=True,
    type=click.INT,
    help="The duration (in seconds) of the custom data recording",
)
@click.option(
    "--mimetype",
    required=True,
    multiple=True,
    help="(Can be given multiple times.) List of mimetypes to attach to the file.",
)
@click.option(
    "--reason",
    required=True,
    type=click.STRING,
    help="The reason this custom data recording was uploaded",
)
@click_argument_path
@pass_memfault_cli_context
def upload_custom_data_recording(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload a custom data recording (read: any file that might help you with debugging)."""
    ctx.obj.update(**kwargs)
    _do_upload_or_raise(ctx, path, CustomDataRecordingUploader)


@cli.command(name="upload-software-version-sbom")
@click.option("--software-type", required=True)
@click.option("--software-version", required=True)
@click_argument_path
@pass_memfault_cli_context
def upload_software_version_sbom(ctx: MemfaultCliClickContext, path: str, **kwargs):
    """Upload an SBOM (Software Bill of Materials) in JSON, XML, or YAML format.

    \b
    Example Software Version SBOM upload:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
            upload-software-version-sbom \\
            --software-type stm32-fw \\
            --software-version 1.0.0-alpha \\
            build/sbom.json

    Reference: https://mflt.io/sboms
    """
    ctx.obj.update(**kwargs)
    _do_upload_or_raise(ctx, path, SoftwareVersionSBOMUploader)


@cli.command(name="deploy-release")
@click.option("--release-version", type=str, required=False)
@click.option("--delta-from", required=False)
@click.option("--delta-to", required=False)
@click.option("--cohort", type=str, required=True)
@click.option(
    "--rollout-percent",
    type=int,
    show_default=True,
    default=100,
    help="The (randomly sampled) percentage of devices in the Cohort to rollout the release to.",
)
@click.option("--deactivate", is_flag=True, help="Deactivate the release.")
@pass_memfault_cli_context
def deploy_release(
    ctx: MemfaultCliClickContext, cohort: str, rollout_percent: int, deactivate: bool, **kwargs
):
    """Publish a Release to a Cohort.

    \b
    Example Release Deployment:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
                   deploy-release \\
                   --release-version 1.0.0-alpha \\
                   --cohort default

    \b
    Example Delta Release Deployment:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
                   deploy-release \\
                   --delta-from 0.9.0 \\
                   --delta-to 1.0.0-alpha \\
                   --cohort default

    \b
    Example Deactivation:
    \b
        $ memfault --org-token $ORG_TOKEN \\
                   --org acme-inc --project smart-sink \\
                   deploy-release \\
                   --release-version 1.0.0-alpha \\
                   --cohort default \\
                   --deactivate
    """
    ctx.obj.update(**kwargs)

    authenticator = ctx.create_authenticator(OrgTokenAuthenticator, BasicAuthenticator)
    ctx.check_required_either(
        {"release_version"}, {"delta_from", "delta_to"}, mutually_exclusive=True
    )
    full_release_version = ctx.obj.get("release_version")
    delta_release_version = (
        ctx.obj["delta_from"],
        ctx.obj["delta_to"],
    )
    release_version = full_release_version or delta_release_version
    deployer = Deployer(ctx=ctx, authenticator=authenticator)
    if deactivate:
        deployer.deactivate(cohort=cohort, release_version=release_version)
    else:
        deployer.deploy(
            cohort=cohort, release_version=release_version, rollout_percent=rollout_percent
        )


def _do_post_chunks_or_raise(ctx: MemfaultCliClickContext, chunks: List[bytes]):
    authenticator = ctx.create_authenticator(ProjectKeyAuthenticator)

    MemfaultChunk(ctx, authenticator).batch_post(chunks)
    click.echo("Success")


@cli.command("post-chunk")
@click.option("--device-serial", show_default=True, default="TESTSERIAL")
@click.option(
    "--encoding",
    type=click.Choice(["hex", "base64", "bin", "sdk_data_export"]),
    required=True,
    help="The format DATA is encoded in.",
)
@click.argument("data")
@pass_memfault_cli_context
def post_chunk(ctx: MemfaultCliClickContext, encoding, data, **kwargs):
    """Sends data generated by the memfault-firmware-sdk ("chunks") to the Memfault cloud.

    The command can operate on binary data encoded in the following formats:

    \b
    1. Hex String:
      memfault --project-key ${YOUR_PROJECT_KEY} post-chunk --encoding hex 0802a702010301076a5445535453455249414c0a6d746573742d736f667477617265096a312e302e302d74657374066d746573742d686172647761726504a101a1726368756e6b5f746573745f737563636573730131e4

    \b
    2. Base64 Encoded String
      memfault --project-key ${YOUR_PROJECT_KEY} post-chunk --encoding base64 CAKnAgEDAQdqVEVTVFNFUklBTAptdGVzdC1zb2Z0d2FyZQlqMS4wLjAtdGVzdAZtdGVzdC1oYXJkd2FyZQShAaFyY2h1bmtfdGVzdF9zdWNjZXNzATHk

    \b
    3. Binary File
      memfault --project-key ${YOUR_PROJECT_KEY} post-chunk --encoding bin chunk_v2_single_chunk_msg.bin

    \b
    4. memfault-firmware-sdk data export
      memfault --project-key ${YOUR_PROJECT_KEY} post-chunk --encoding sdk_data_export data_export.txt

    Reference: https://mflt.io/chunk-api-integration
    """

    ctx.obj.update(**kwargs)
    if encoding == "hex":
        chunks = [bytes.fromhex(data)]
    elif encoding == "base64":
        chunks = [b64decode(data)]
    elif encoding == "bin":
        with click.open_file(data, "rb") as f:
            chunks = [f.read()]
    elif encoding == "sdk_data_export":
        with click.open_file(data, "r") as f:
            exported_data = f.read()
        chunks = MemfaultChunk.extract_exported_chunks(exported_data)
        if len(chunks) == 0:
            raise click.exceptions.UsageError(f"No Memfault chunks found in {data}")
        click.echo(f"Found {len(chunks)} Chunks. Sending Data ...")
    else:
        raise click.exceptions.UsageError(f"Unsupported encoding: {encoding}")

    _do_post_chunks_or_raise(ctx, chunks)


@cli.command("completion")
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    required=True,
    help="select shell type for completion script",
)
@click.pass_context
def completion(ctx, shell: str):
    """
    Generate shell completion script for memfault.

    \b
    Example:
    \b
        $ memfault completion --shell bash > ~/.memfault_completion.bash
        $ echo 'source ~/.memfault_completion.bash' >> ~/.bashrc

    """

    # re-invoke the main cli entrance point after setting the Click completion
    # environment variable. it's necessary to do this via the Click ctx so that
    # it works properly when invoked from pytest or normal cli usage.

    cmd = "memfault"
    os.environ[f"_{cmd.upper()}_COMPLETE"] = f"{shell}_source"
    ctx.command.main(prog_name="memfault")


@cli.command("console")
@click.option("--device-serial", show_default=True, default="TESTSERIAL")
@click.option(
    "--port",
    help="Serial port to read data from. Omit to choose from list of detected ports",
    default=None,
)
@click.option("--baudrate", help="baud rate, default: 115200", default=115200)
@pass_memfault_cli_context
def console(ctx: MemfaultCliClickContext, port, baudrate, **kwargs):
    """
    Open a serial terminal and automatically post chunks to Memfault
    The command requires output produced by memfault_data_export_chunk.

    \b
    $ memfault --project-key ${YOUR_PROJECT_KEY} console --device-serial TESTSERIAL --port /dev/tty.usbmodem1

    \b
    Example Output:
    my_log: exporting memfault chunks
    MC:CAKnAgEDAQdqVEVTVFNFUklBTAptdGVzdC1zb2Z0d2FyZQlqMS4wLjAtdGVzdAZtdGVzdC1oYXJkd2FyZQShAaFyY2h1bmtfdGVzdF9zdWNjZXNzATHk:
    [MFLT CONSOLE]: Sending 1 chunks to Memfault cloud
    [MFLT CONSOLE]: Success

    Reference: https://mflt.io/chunk-api-integration
    """
    from serial.tools import miniterm

    if port is None:
        port = miniterm.ask_for_port()

    ctx.obj.update(**kwargs)

    # Build chunk-poster
    authenticator = ctx.create_authenticator(ProjectKeyAuthenticator)
    chunk_handler: MemfaultChunk
    if not authenticator.project_key_auth():
        click.secho(
            "Use 'memfault --project-key=${PROJECT_KEY} console' to automatically upload chunks",
            fg="yellow",
        )
        chunk_handler = None  # pyright: ignore[reportAssignmentType]
    else:
        chunk_handler = MemfaultChunk(ctx, authenticator)

    MemfaultMiniterm.from_port(chunk_handler=chunk_handler, port=port, baudrate=baudrate)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # optionally set terminal to infinite width for consistent click output
    # formatting
    terminal_width = float("inf") if os.environ.get("CI") else None
    cli(auto_envvar_prefix="MEMFAULT", terminal_width=terminal_width)


if __name__ == "__main__":
    main()
