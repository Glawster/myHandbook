from pathlib import Path

import pytest

from fmparser.structures import AssetInfo

pytest.importorskip("PySide6")

from PySide6.QtCore import QCoreApplication, Qt  # noqa: E402

from fmparser.qtBundleExplorer import AssetFilterProxyModel, AssetTableModel  # noqa: E402


def _applicationCreate() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


def _assetCreate(path_id: int, name: str, asset_type: str) -> AssetInfo:
    return AssetInfo(
        bundle_path=Path("sample.bundle"),
        path_id=path_id,
        asset_name=name,
        asset_type=asset_type,
        container_path=f"ui/{name}.asset",
        serialized_size=path_id,
    )


def testAssetTableModelExposesColumns() -> None:
    _applicationCreate()
    model = AssetTableModel((_assetCreate(2, "Beta", "Texture2D"),))

    assert model.rowCount() == 1
    assert model.columnCount() == 6
    assert model.headerData(0, Qt.Orientation.Horizontal) == "Path ID"
    assert model.data(model.index(0, 1)) == "Beta"


def testAssetFilterProxyFiltersAssets() -> None:
    _applicationCreate()
    model = AssetTableModel(
        (
            _assetCreate(1, "PlayerPanel", "VisualTreeAsset"),
            _assetCreate(2, "PlayerIcon", "Texture2D"),
        )
    )
    proxy = AssetFilterProxyModel()
    proxy.setSourceModel(model)

    proxy.filtersSet(text="player", asset_type="VisualTree")

    assert proxy.rowCount() == 1
    assert proxy.data(proxy.index(0, 1)) == "PlayerPanel"
