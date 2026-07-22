import zlib

from fmparser.compression import compressionProbe


def test_probe_compression_reports_success() -> None:
    payload = zlib.compress(b"football manager tactic")

    attempts = compressionProbe(payload)

    assert any(item.algorithm == "zlib" and item.success for item in attempts)
