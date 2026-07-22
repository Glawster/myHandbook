"""Differential analysis for controlled FMF experiments."""

from __future__ import annotations

from itertools import zip_longest
from pathlib import Path

from fmparser.structures import Change, ChangeGroup


def bytesChanged(old: bytes, new: bytes) -> tuple[Change, ...]:
    """Return byte-level changes between two byte strings."""
    changes: list[Change] = []
    sentinel = object()
    for offset, (old_byte, new_byte) in enumerate(zip_longest(old, new, fillvalue=sentinel)):
        if old_byte == new_byte:
            continue
        changes.append(
            Change(
                offset=offset,
                old=None if old_byte is sentinel else int(old_byte),
                new=None if new_byte is sentinel else int(new_byte),
            )
        )
    return tuple(changes)


def changesGroup(changes: tuple[Change, ...], *, maxGap: int = 8) -> tuple[ChangeGroup, ...]:
    """Group nearby byte changes into contiguous comparison regions."""
    if not changes:
        return ()
    groups: list[ChangeGroup] = []
    current = [changes[0]]
    for change in changes[1:]:
        if change.offset - current[-1].offset <= maxGap:
            current.append(change)
        else:
            groups.append(_make_group(current))
            current = [change]
    groups.append(_make_group(current))
    return tuple(groups)


def filesDiff(oldPath: str | Path, newPath: str | Path) -> tuple[ChangeGroup, ...]:
    """Read and compare two files, returning grouped byte changes."""
    old = Path(oldPath).read_bytes()
    new = Path(newPath).read_bytes()
    return changesGroup(bytesChanged(old, new))


def _make_group(changes: list[Change]) -> ChangeGroup:
    span = changes[-1].offset - changes[0].offset + 1
    if len(changes) == span:
        likely = "contiguous byte range"
    elif len(changes) <= 4:
        likely = "small scalar field or checksum ripple"
    else:
        likely = "clustered structure or compressed/checksummed payload"
    return ChangeGroup(
        start=changes[0].offset,
        end=changes[-1].offset,
        changes=tuple(changes),
        likely_structure=likely,
    )
