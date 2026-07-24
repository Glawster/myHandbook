"""Tests for batch session orchestration."""

from pathlib import Path

from scripts.buildSessions import sessionsBuild


def test_sessionsBuildDryRunDoesNotCreateOutput(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "01-passing.yaml").write_text(
        """
sessionNumber: 1
sessionTitle: Passing
theme: Passing
keyPhrase: Pass.
duration: 60 minutes
players: "8"
equipment: [Balls]
objectives: [Pass accurately]
""".strip(),
        encoding="utf-8",
    )
    output = tmp_path / "generated"

    summary = sessionsBuild(
        tmp_path / "unused-template.odt",
        sessions,
        output,
        dryRun=True,
    )

    assert summary.discovered == 1
    assert summary.built == 1
    assert not output.exists()
