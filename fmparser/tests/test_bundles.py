import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from fmparser.bundles import BundleFormatError, UnityPyBundleReader


class _Type:
    name = "TextAsset"


class _Object:
    path_id = 123
    type = _Type()
    byte_size = 42

    def peek_name(self) -> str:
        return "hello"

    def read(self) -> SimpleNamespace:
        return SimpleNamespace(name="hello", script=b"hello world")

    def read_typetree(self) -> dict[str, str]:
        return {"m_Name": "hello"}


def testBundleReaderValidatesMissingPath(tmp_path: Path) -> None:
    reader = UnityPyBundleReader()

    with pytest.raises(FileNotFoundError):
        reader.open(tmp_path / "missing.bundle")


def testBundleReaderConvertsAdapterErrors(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    sample = tmp_path / "sample.bundle"
    sample.write_bytes(b"UnityFS\x00")

    def load(path: str) -> object:
        del path
        raise ValueError("bad bundle")

    monkeypatch.setitem(sys.modules, "UnityPy", SimpleNamespace(load=load))

    with pytest.raises(BundleFormatError, match="Could not open Unity bundle"):
        UnityPyBundleReader().open(sample)


def testBundleReaderListsAndReadsAssets(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    sample = tmp_path / "sample.bundle"
    sample.write_bytes(b"UnityFS\x00")
    unity_object = _Object()
    environment = SimpleNamespace(
        objects=[unity_object],
        container={"assets/ui/hello.txt": unity_object},
        unity_version="6000.0",
        files=[],
    )
    monkeypatch.setitem(sys.modules, "UnityPy", SimpleNamespace(load=lambda path: environment))

    reader = UnityPyBundleReader()
    info = reader.open(sample)
    assets = reader.assetsList()
    data = reader.assetRead(123)
    search_text = reader.assetSearchText(123)

    assert info.signature == "UnityFS"
    assert info.asset_count == 1
    assert info.unity_version == "6000.0"
    assert assets[0].path_id == 123
    assert assets[0].asset_name == "hello"
    assert assets[0].container_path == "assets/ui/hello.txt"
    assert data.text == "hello world"
    assert data.representation == "original-or-serialized-text"
    assert "hello world" in search_text
    assert "m_name" in search_text
