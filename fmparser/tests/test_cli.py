from pathlib import Path

from fmparser.cli import main


def test_cli_hex(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    sample = tmp_path / "sample.fmf"
    sample.write_bytes(b"abcdef")

    assert main(["hex", str(sample), "--length", "6"]) == 0
    assert "61 62 63" in capsys.readouterr().out
