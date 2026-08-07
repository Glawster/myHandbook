"""Tests for YAML session parsing."""

from pathlib import Path

import pytest

from scripts.builderErrors import SessionDataError
from scripts.sessionParser import sessionParse


def test_sessionParseBuildsTypedSession(tmp_path: Path) -> None:
    source = tmp_path / "02-firstTouch.yaml"
    source.write_text(
        """
sessionNumber: 2
sessionTitle: First Touch & Movement
theme: First Touch
keyPhrase: Pass. Move. Receive.
duration: 60 minutes
players: 8-16
equipment:
  - Balls
  - Bibs
objectives:
  - Receive with control
  - Move after passing
""".strip(),
        encoding="utf-8",
    )

    session = sessionParse(source)

    assert session.sessionNumber == 2
    assert session.equipment == ("Balls", "Bibs")
    assert session.placeholdersBuild()["objectives"] == "Receive with control\nMove after passing"


def test_sessionParseRejectsUnknownField(tmp_path: Path) -> None:
    source = tmp_path / "invalid.yaml"
    source.write_text(
        """
sessionNumber: 1
sessionTitle: Passing
theme: Passing
keyPhrase: Pass.
duration: 60 minutes
players: 8
equipment: [Balls]
objectives: [Pass accurately]
unexpected: value
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(SessionDataError, match="unknown fields: unexpected"):
        sessionParse(source)
