import zlib

from fmparser.compression import probe_compression


def test_probe_compression_reports_success() -> None:
    payload = zlib.compress(b"football manager tactic")

    attempts = probe_compression(payload)

    assert any(item.algorithm == "zlib" and item.success for item in attempts)
