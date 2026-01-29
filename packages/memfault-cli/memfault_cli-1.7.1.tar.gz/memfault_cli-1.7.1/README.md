# Memfault CLI tool

This package contains the `memfault` CLI tool.

The purpose of the tool is to make integration with Memfault from other systems,
like continuous integration servers, as easy as possible.

Install the tool and run `memfault --help` for more info!

## Changes

### [1.7.1] - 2026-01-13

- Update `urllib3` dependency to `>=2.6.3` to address
  [this security disclosure](https://www.cve.org/CVERecord?id=CVE-2026-21441).

### [1.7.0] - 2025-12-15

- Update `urllib3` dependency to `>=2.6.2` to address
  [this security disclosure](https://nvd.nist.gov/vuln/detail/CVE-2025-66418).

- Update `tqdm` dependency to `>=4.67.1` to address
  [this security disclosure](https://nvd.nist.gov/vuln/detail/CVE-2024-34062).

- Update `requests` dependency to `>=2.32.4` to address the following
  disclosures:

  - [CVE-2023-32681](https://nvd.nist.gov/vuln/detail/CVE-2023-32681)
  - [CVE-2024-35195](https://nvd.nist.gov/vuln/detail/CVE-2024-35195)
  - [CVE-2024-47081](https://nvd.nist.gov/vuln/detail/CVE-2024-47081)

- Remove support for Python 3.8. The minimum required Python version is now 3.9.

### [1.6.0] - 2025-04-23

- Add support for uploading ELF files without DWARF debug info.

### [1.5.0] - 2024-11-14

- Add support for Python 3.13: remove unnecessary version constraints on the
  `chardet` + `lxml` dependencies.

### [1.4.0] - 2024-11-12

- Populate a User-Agent string in the headers of all requests to Memfault Cloud
  to identify the CLI version used for diagnostics. Previously the User-Agent
  was only included for chunk POST requests.

### [1.3.0] - 2024-11-07

- Remove support for Python 3.6 + 3.7

### [1.2.0] - 2024-08-28

- Add the `upload-software-version-sbom` command. Look at the
  [SBOM docs](https://docs.memfault.com/docs/platform/sbom) for more info.

### [1.1.0] - 2024-07-22

- Add a user-agent string to chunk POST requests to identify CLI version used
  for diagnostics.

- Fixups with ruff (RET504)

### [1.0.11] - 2024-06-28

- Add an option `--no-check-uploaded` for `upload-mcu-symbols` to skip an
  initial check if the symbol file already exists. This option should be used
  with Org Tokens limited to only uploading symbol file

- Bump urllib3 dependency to 1.26.19

- Fixups with ruff 0.4.10

### [1.0.10] - 2024-06-13

- Source pyelftools from <https://pypi.org/project/pyelftools/> again, as the
  required bugfixes have been merged upstream. See notes of 1.0.6 below.

### [1.0.9] - 2024-04-04

- Add Miniterm help text when launching the `memfault console` command, to
  indicate how to exit the console (`Ctrl-]`).

### 1.0.8

- Add Apache 2 license

### 1.0.7

- Fix bug when deactivating delta releases when multiple deployments match the
  filters.

### 1.0.6

- Source pyelftools from <https://github.com/memfault/pyelftools> while we are
  waiting for 2 bugfixes to get merged upstream
  (<https://github.com/eliben/pyelftools/pull/537> and
  <https://github.com/eliben/pyelftools/pull/538>).

### 1.0.5

- Add support for deactivating delta releases.

### 1.0.4

- Add `upload-elf-symbols` command for uploading ELF files with debug symbols
  built outside of a Yocto environment
- Add `upload-elf-coredump` for uploading a Linux coredump to Memfault

### 1.0.3

- Fix a bug where `upload-aosp-symbols` would fail when uploading too many files
  at once.

### 1.0.2

- Fix a bug where `upload-yocto-symbols` would fail when some files in the
  tarballs provided did not have the read permission set.

### 1.0.1

- Fix `upload-custom-data-recording` to print a more helpful error message when
  exceeding device rate limits.

### 1.0.0

_Note: this release is marked as `1.0.0` but does not contain any breaking
changes! The version number was bumped to reflect the maturity of the tool._

- Fix `upload-mcu-symbols` to skip uploading if the symbol file has already been
  uploaded, and return a zero exit code in this case

### 0.18.1

- Add the `--deactivate` option to `deploy-release`, which disables a release
  for a cohort

### 0.18.0

- Add new `extra-metadata` option to `upload-ota-payload` to attach custom
  metadata to that OTA release. The metadata will be returned from Memfault
  Cloud when fetching the latest Android OTA release.
- Continue uploading the entire folder of symbols even if any single upload
  fails due to the symbol file being too large.

### 0.17.0

- Add new `console` command to read SDK exported chunks via a serial port and
  automatically upload to Memfault.

### 0.16.0

- Add support for uploading Android debug symbols from alternative build
  systems.

### 0.15.3

- Warn if a non-slug string is passed to the `--project` or `--org` arguments

### 0.15.2

- Don't truncate help output from `click` when the `CI` environment variable is
  set, for consistent output formatting

### 0.15.1

- Fix some compatibility issues for python3.6 + python3.7

### 0.15.0

- 💥 Breaking change: update the `upload-yocto-symbols` subcommand to take two
  image paths as required arguments; one for the root filesystem image, and
  another for the debug filesystem image. Versions 0.14.0 and lower used to take
  a guess at the path of the debug filesystem image from the value passed to the
  `--image` param. To avoid confusion and to support all configurations, the
  Memfault CLI no longer does any guessing and now takes two separate params:
  `--image` and `--dbg-image`

### 0.14.0

- ✨ Update the `post-chunk` subcommand to split uploads into batches of 500
  chunks per upload, to avoid timing out when uploading very large chunk logs

### 0.13.0

- 💥 Breaking change: Renamed subcommand `upload-debug-data-recording` to
  `custom-data-recording`

### 0.12.0

- ✨ Added subcommand `upload-debug-data-recording` for uploading debug data
  files

### 0.11.0

- ✨ Enable support for Yocto Dunfell based projects (previously supported
  Kirkstone only)

### 0.10.0

- ✨ Upload-yocto-symbols now uploads additional symbol files

### 0.9.0

- ✨ Expanded support for .elf uploading with the upload-yocto-symbols
  subcommand

### 0.8.0

- ✨ Initial support for upload-yocto-symbols subcommand

### 0.7.0

- 🐛 Updated to correctly only use the GNU build-id `.note` section
