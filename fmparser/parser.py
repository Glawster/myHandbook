"""High-level file inspection and placeholder tactic parser."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import logging
from pathlib import Path

from fmparser.compression import compressionProbe
from fmparser.signatures import asciiStrings, entropy, entropyWindows, headerInfo, sectionCandidates
from fmparser.structures import FileInspection, PlayerSlot, TacticMetadata

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FMFTactic:
    """Parsed tactic model.

    Most fields are intentionally optional at this stage. As byte mappings are proven, they should
    be promoted from ``unknown`` into typed properties with evidence in
    ``documentation/reverseEngineering.md``.
    """

    metadata: TacticMetadata
    formation: str | None = None
    mentality: str | None = None
    players: tuple[PlayerSlot, ...] = ()
    team_instructions: tuple[str, ...] = ()
    player_instructions: dict[str, tuple[str, ...]] = field(default_factory=dict)
    unknown: dict[str, int | str | bytes] = field(default_factory=dict)

    @classmethod
    def read(cls, path: str | Path) -> FMFTactic:
        return FMFParser().parse(path)


class FMFParser:
    """Entry point for inspecting and parsing FMF files."""

    def inspect(self, path: str | Path) -> FileInspection:
        file_path = Path(path)
        data = file_path.read_bytes()
        LOGGER.info("inspecting %s (%d bytes)", file_path, len(data))
        possibleOffsets = tuple(sorted({0, *[item.offset for item in sectionCandidates(data)[:10]]}))
        return FileInspection(
            path=file_path,
            size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            header=headerInfo(data),
            entropy=entropy(data),
            entropy_windows=entropyWindows(data),
            strings=asciiStrings(data),
            sections=sectionCandidates(data),
            compression_attempts=compressionProbe(data, offsets=possibleOffsets),
        )

    def parse(self, path: str | Path) -> FMFTactic:
        file_path = Path(path)
        data = file_path.read_bytes()
        LOGGER.info("creating low-confidence tactic model for %s", file_path)
        return FMFTactic(
            metadata=TacticMetadata(
                filename=file_path.name,
                size=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
            ),
            unknown={
                "header_hex": data[:32].hex(" "),
                "known_fields": "none-yet",
            },
        )
