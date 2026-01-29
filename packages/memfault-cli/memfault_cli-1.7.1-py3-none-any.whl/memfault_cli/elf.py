import dataclasses
import pathlib
from typing import BinaryIO, Iterable, Optional

import more_itertools
from elftools.common.exceptions import ELFError
from elftools.construct import Container
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import NoteSection
from elftools.elf.segments import NoteSegment

# TODO: Deduplicate. Copy pasta from elf_utils.py

NT_GNU_BUILD_ID = "NT_GNU_BUILD_ID"

ELF_NOTE_SECTION_OWNER_GNU = "GNU"


def is_elf(file: BinaryIO) -> bool:
    magic = file.read(4)
    return magic == b"\x7fELF"


def elf_has_debug_info(elf: ELFFile) -> bool:
    # Note: not using .has_dwarf_info() because it will return True if .eh_frame is present.
    # This section is usually kept in stripped binaries, because certain languages (C++) depend on it at runtime.
    return bool(elf.get_section_by_name(".debug_info") or elf.get_section_by_name(".zdebug_info"))


def elf_has_text(elf: ELFFile) -> bool:
    """
    .elfs can be "split" into a .debug_info file and one that contains the code (w/o .debug_info).
    This function takes a guess at whether the file contains code by looking at whether common sections contain data.
    """
    for section_name in [".text", ".rodata", ".data"]:
        section = elf.get_section_by_name(section_name)
        # Note: if .text/etc. are stripped off, the type is SHT_NOBITS
        if section is not None and section.header["sh_type"] == "SHT_PROGBITS":
            return True
    return False


@dataclasses.dataclass(frozen=True)
class ELFFileInfo:
    path: pathlib.Path
    """The path to the .elf file"""

    relpath: pathlib.Path
    """The path to the .elf file relative to the a root path"""

    has_debug_info: bool
    """True if the .elf contains .debug_info and/or .zdebug_info sections."""

    has_text: bool
    """True if the .elf contains PROGBITS for .text, .rodata and/or .data sections."""

    gnu_build_id: Optional[str]
    """The GNU Build ID if found"""


def find_elf_files(
    dir: pathlib.Path,  # noqa: A002
    *,
    relative_to: pathlib.Path,
    recurse: bool = True,
    follow_symlinks: bool = False,
) -> Iterable[ELFFileInfo]:
    if not dir.is_dir() or not dir.exists():
        return
    if not follow_symlinks and dir.is_symlink():
        return
    for path in dir.iterdir():
        if not follow_symlinks and path.is_symlink():
            continue
        if path.is_dir() and recurse:
            yield from find_elf_files(
                path, relative_to=relative_to, recurse=recurse, follow_symlinks=follow_symlinks
            )
        elif path.is_file():
            with open(path, "rb") as f:
                if not is_elf(f):  # Cheap check
                    continue
                try:
                    elf = ELFFile(f)
                except ELFError:
                    continue
                info = ELFFileInfo(
                    path=path,
                    relpath=path.relative_to(relative_to),
                    has_debug_info=elf_has_debug_info(elf),
                    has_text=elf_has_text(elf),
                    gnu_build_id=get_gnu_build_id(elf),
                )
            yield info


def get_note_segments(elf: ELFFile) -> Iterable[NoteSegment]:
    return filter(lambda segment: isinstance(segment, NoteSegment), elf.iter_segments())


def get_note_sections(elf: ELFFile) -> Iterable[NoteSection]:
    return filter(lambda segment: isinstance(segment, NoteSection), elf.iter_sections())


def get_notes(elf: ELFFile) -> Iterable[Container]:
    for note_segment in get_note_segments(elf):
        yield from note_segment.iter_notes()
    for note_section in get_note_sections(elf):
        yield from note_section.iter_notes()


def is_gnu_build_id_note_section(section: Container) -> bool:
    return (section.n_type == NT_GNU_BUILD_ID) and (section.n_name == ELF_NOTE_SECTION_OWNER_GNU)


def get_gnu_build_id(elf: ELFFile) -> Optional[str]:
    build_id_note = more_itertools.first_true(
        get_notes(elf),
        pred=is_gnu_build_id_note_section,
    )
    if not build_id_note:
        return None
    return build_id_note.n_desc
