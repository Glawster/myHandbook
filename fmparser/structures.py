"""Dataclasses that describe known and unknown FMF structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EntropyWindow:
    offset: int
    length: int
    entropy: float
    classification: str


@dataclass(frozen=True)
class ASCIIString:
    offset: int
    value: str


@dataclass(frozen=True)
class HeaderInfo:
    magic_hex: str
    magic_ascii: str
    version: str | None
    flags: dict[str, int | str] = field(default_factory=dict)


@dataclass(frozen=True)
class SectionCandidate:
    offset: int
    length: int
    confidence: float
    reason: str


@dataclass(frozen=True)
class CompressionAttempt:
    algorithm: str
    offset: int
    input_length: int
    success: bool
    output_length: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class Change:
    offset: int
    old: int | None
    new: int | None


@dataclass(frozen=True)
class ChangeGroup:
    start: int
    end: int
    changes: tuple[Change, ...]
    likely_structure: str


@dataclass(frozen=True)
class RepeatedStructureCandidate:
    offset: int
    record_length: int
    count: int
    confidence: float
    reason: str


@dataclass(frozen=True)
class TacticMetadata:
    filename: str
    size: int
    sha256: str


@dataclass(frozen=True)
class PlayerSlot:
    position: str
    role: str | None = None
    duty: str | None = None
    raw: dict[str, int | str] = field(default_factory=dict)


@dataclass(frozen=True)
class FileInspection:
    path: Path
    size: int
    sha256: str
    header: HeaderInfo
    entropy: float
    entropy_windows: tuple[EntropyWindow, ...]
    strings: tuple[ASCIIString, ...]
    sections: tuple[SectionCandidate, ...]
    compression_attempts: tuple[CompressionAttempt, ...]
