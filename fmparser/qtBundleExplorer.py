"""PySide6 prototype for inspecting Football Manager skin bundles."""

from __future__ import annotations

import sys
import traceback
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fmparser.bundleFilter import assetsFilter
from fmparser.bundles import BundleError, UnityPyBundleReader
from fmparser.structures import AssetData, AssetInfo, BundleInfo

try:
    from PySide6.QtCore import (
        QAbstractTableModel,
        QModelIndex,
        QObject,
        QSettings,
        QSortFilterProxyModel,
        Qt,
        QRunnable,
        QThreadPool,
        Signal,
        Slot,
    )
    from PySide6.QtGui import QAction, QKeySequence
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QSplitter,
        QStatusBar,
        QTableView,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )
except ImportError as error:  # pragma: no cover - exercised only without optional dependency.
    raise BundleError("PySide6 is required for the Qt prototype. Install with `pip install .[gui]`.") from error


class AssetTableModel(QAbstractTableModel):
    """Qt table model for bundle asset metadata."""

    COLUMNS = ("Path ID", "Name", "Type", "Container", "Size", "References")

    def __init__(self, assets: Sequence[AssetInfo] | None = None) -> None:
        super().__init__()
        self._assets = list(assets or ())

    def assetsSet(self, assets: Sequence[AssetInfo]) -> None:
        self.beginResetModel()
        self._assets = list(assets)
        self.endResetModel()

    def assetAt(self, row: int) -> AssetInfo | None:
        if row < 0 or row >= len(self._assets):
            return None
        return self._assets[row]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._assets)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.UserRole):
            return None
        asset = self._assets[index.row()]
        values = (
            asset.path_id,
            asset.asset_name or "",
            asset.asset_type,
            asset.container_path or "",
            asset.serialized_size if asset.serialized_size is not None else "",
            len(asset.dependencies) + len(asset.external_references),
        )
        return values[index.column()]

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        reverse = order == Qt.SortOrder.DescendingOrder
        self.layoutAboutToBeChanged.emit()
        self._assets.sort(key=lambda asset: _sortValue(asset, column), reverse=reverse)
        self.layoutChanged.emit()


class AssetFilterProxyModel(QSortFilterProxyModel):
    """Filter asset rows by text and optional type text."""

    def __init__(self) -> None:
        super().__init__()
        self._text = ""
        self._asset_type = ""
        self._serialized_text_by_id: dict[int, str] = {}

    def filtersSet(self, *, text: str, asset_type: str) -> None:
        self._text = text
        self._asset_type = asset_type
        self._invalidate()

    def serializedSearchTextSet(self, values: dict[int, str]) -> None:
        self._serialized_text_by_id = dict(values)
        self._invalidate()

    def _invalidate(self) -> None:
        if hasattr(self, "invalidate"):
            self.invalidate()
        else:  # pragma: no cover - compatibility with older PySide6 releases.
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        model = self.sourceModel()
        if not isinstance(model, AssetTableModel):
            return True
        asset = model.assetAt(source_row)
        if asset is None:
            return False
        if not assetsFilter((asset,), text="", asset_type=self._asset_type):
            return False
        query = self._text.strip().casefold()
        if not query:
            return True
        if assetsFilter((asset,), text=self._text, asset_type=""):
            return True
        return query in self._serialized_text_by_id.get(asset.path_id, "")


class _OpenSignals(QObject):
    finished = Signal(object, object, object)
    failed = Signal(str, str)


class _OpenBundleWorker(QRunnable):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.signals = _OpenSignals()

    @Slot()
    def run(self) -> None:
        try:
            reader = UnityPyBundleReader()
            info = reader.open(self.path)
            assets = tuple(reader.assetsList())
        except Exception as error:  # noqa: BLE001 - send readable dialog plus log detail.
            self.signals.failed.emit(str(error), traceback.format_exc())
            return
        self.signals.finished.emit(info, assets, reader)


class _PreviewSignals(QObject):
    finished = Signal(object)
    failed = Signal(str, str)


class _PreviewWorker(QRunnable):
    def __init__(self, reader: UnityPyBundleReader, asset_id: int) -> None:
        super().__init__()
        self.reader = reader
        self.asset_id = asset_id
        self.signals = _PreviewSignals()

    @Slot()
    def run(self) -> None:
        try:
            data = self.reader.assetRead(self.asset_id)
        except Exception as error:  # noqa: BLE001 - send readable dialog plus log detail.
            self.signals.failed.emit(str(error), traceback.format_exc())
            return
        self.signals.finished.emit(data)


class _DeepSearchSignals(QObject):
    finished = Signal(int, object)
    failed = Signal(str, str)


class _DeepSearchWorker(QRunnable):
    def __init__(
        self,
        reader: UnityPyBundleReader,
        assets: Sequence[AssetInfo],
        generation: int,
    ) -> None:
        super().__init__()
        self.reader = reader
        self.assets = tuple(assets)
        self.generation = generation
        self.signals = _DeepSearchSignals()

    @Slot()
    def run(self) -> None:
        try:
            values = {
                asset.path_id: self.reader.assetSearchText(asset.path_id)
                for asset in self.assets
            }
        except Exception as error:  # noqa: BLE001 - send readable dialog plus log detail.
            self.signals.failed.emit(str(error), traceback.format_exc())
            return
        self.signals.finished.emit(self.generation, values)


class BundleExplorerWindow(QMainWindow):
    """Initial read-only bundle explorer window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FM26 Skin Bundle Explorer")
        self._settings = QSettings("myHandbook", "fmparser-bundle-explorer")
        self._thread_pool = QThreadPool.globalInstance()
        self._reader: UnityPyBundleReader | None = None
        self._bundle_path: Path | None = None
        self._assets: tuple[AssetInfo, ...] = ()
        self._deep_search_generation = 0
        self._deep_search_running = False

        self._model = AssetTableModel()
        self._proxy = AssetFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.selectionModel().currentRowChanged.connect(self._assetSelected)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter name, type, container, or path ID")
        self._filter.textChanged.connect(self._filtersChanged)
        self._type_filter = QLineEdit()
        self._type_filter.setPlaceholderText("Type filter")
        self._type_filter.textChanged.connect(self._filtersChanged)
        self._type_summary = QListWidget()
        self._type_summary.setMaximumHeight(130)
        self._type_summary.itemClicked.connect(self._typeSummaryClicked)

        self._metadata = QPlainTextEdit()
        self._metadata.setReadOnly(True)
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(500)

        self._actionsBuild()
        self._layoutBuild()
        self.setStatusBar(QStatusBar())
        self._settingsRestore()

    def bundleOpen(self, path: Path) -> None:
        self._busySet(f"Opening {path}")
        worker = _OpenBundleWorker(path)
        worker.signals.finished.connect(self._bundleOpened)
        worker.signals.failed.connect(self._workerFailed)
        self._thread_pool.start(worker)

    def bundleClose(self) -> None:
        self._reader = None
        self._bundle_path = None
        self._assets = ()
        self._deep_search_generation += 1
        self._deep_search_running = False
        self._model.assetsSet(())
        self._proxy.serializedSearchTextSet({})
        self._typeSummarySet(())
        self._metadata.clear()
        self._preview.clear()
        self.statusBar().showMessage("Bundle closed")

    def _actionsBuild(self) -> None:
        toolbar = QToolBar("Bundle")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("Open Bundle", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._bundleChoose)
        toolbar.addAction(open_action)

        close_action = QAction("Close Bundle", self)
        close_action.triggered.connect(self.bundleClose)
        toolbar.addAction(close_action)

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._bundleRefresh)
        toolbar.addAction(refresh_action)

        copy_action = QAction("Copy Metadata", self)
        copy_action.triggered.connect(self._metadataCopy)
        toolbar.addAction(copy_action)

    def _layoutBuild(self) -> None:
        filters = QHBoxLayout()
        filters.addWidget(QLabel("Search"))
        filters.addWidget(self._filter, 2)
        filters.addWidget(QLabel("Type"))
        filters.addWidget(self._type_filter, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addLayout(filters)
        left_layout.addWidget(self._type_summary)
        left_layout.addWidget(self._table)

        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(self._metadata)
        right.addWidget(self._preview)
        right.addWidget(self._log)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([750, 450])
        self.setCentralWidget(splitter)

    def _settingsRestore(self) -> None:
        geometry = self._settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.resize(1200, 760)

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("last_bundle_dir", str(self._bundle_path.parent) if self._bundle_path else "")
        super().closeEvent(event)

    def _bundleChoose(self) -> None:
        start = str(self._settings.value("last_bundle_dir", ""))
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Unity Bundle",
            start,
            "Unity bundles (*.bundle);;All files (*)",
        )
        if file_name:
            self.bundleOpen(Path(file_name))

    def _bundleRefresh(self) -> None:
        if self._bundle_path is not None:
            self.bundleOpen(self._bundle_path)

    def _filtersChanged(self) -> None:
        self._proxy.filtersSet(text=self._filter.text(), asset_type=self._type_filter.text())
        self._deepSearchMaybeStart()

    def _typeSummaryClicked(self, item: QListWidgetItem) -> None:
        asset_type = item.data(Qt.ItemDataRole.UserRole)
        self._type_filter.setText(str(asset_type or ""))

    def _assetSelected(self, current: QModelIndex, previous: QModelIndex) -> None:
        del previous
        if self._reader is None or not current.isValid():
            return
        source_index = self._proxy.mapToSource(current)
        asset = self._model.assetAt(source_index.row())
        if asset is None:
            return
        self._metadata.setPlainText(_metadataText(asset))
        self._preview.setPlainText("Loading preview...")
        worker = _PreviewWorker(self._reader, asset.path_id)
        worker.signals.finished.connect(self._previewReady)
        worker.signals.failed.connect(self._workerFailed)
        self._thread_pool.start(worker)

    def _metadataCopy(self) -> None:
        QApplication.clipboard().setText(self._metadata.toPlainText())
        self.statusBar().showMessage("Metadata copied", 2500)

    def _bundleOpened(
        self,
        info: BundleInfo,
        assets: tuple[AssetInfo, ...],
        reader: UnityPyBundleReader,
    ) -> None:
        self._reader = reader
        self._bundle_path = info.path
        self._assets = assets
        self._deep_search_generation += 1
        self._deep_search_running = False
        self._settings.setValue("last_bundle_dir", str(info.path.parent))
        self._model.assetsSet(assets)
        self._proxy.serializedSearchTextSet({})
        self._typeSummarySet(assets)
        self._metadata.setPlainText(_bundleText(info))
        self._preview.clear()
        self._log.appendPlainText(f"Opened {info.file_name}: {info.asset_count} assets")
        self.statusBar().showMessage(f"Opened {info.file_name}")

    def _previewReady(self, data: AssetData) -> None:
        self._metadata.setPlainText(_metadataText(data.asset))
        preview = data.text or data.message or "No readable preview is available."
        if data.message and data.text:
            preview = f"{data.message}\n\n{data.text}"
        self._preview.setPlainText(preview)
        self.statusBar().showMessage(f"Selected asset {data.asset.path_id}", 2500)

    def _workerFailed(self, message: str, detail: str) -> None:
        self._log.appendPlainText(detail)
        self.statusBar().showMessage("Bundle operation failed")
        QMessageBox.warning(self, "Bundle Explorer", message)

    def _busySet(self, message: str) -> None:
        self.statusBar().showMessage(message)
        self._log.appendPlainText(message)

    def _deepSearchMaybeStart(self) -> None:
        if self._reader is None or self._deep_search_running or not self._filter.text().strip():
            return
        self._deep_search_running = True
        generation = self._deep_search_generation
        worker = _DeepSearchWorker(self._reader, self._assets, generation)
        worker.signals.finished.connect(self._deepSearchReady)
        worker.signals.failed.connect(self._workerFailed)
        self._thread_pool.start(worker)
        self.statusBar().showMessage("Building serialized search cache...")

    def _deepSearchReady(self, generation: int, values: dict[int, str]) -> None:
        if generation != self._deep_search_generation:
            return
        self._deep_search_running = False
        self._proxy.serializedSearchTextSet(values)
        self.statusBar().showMessage("Serialized search cache ready", 2500)

    def _typeSummarySet(self, assets: Sequence[AssetInfo]) -> None:
        self._type_summary.clear()
        for asset_type, count in _typeCounts(assets):
            item = QListWidgetItem(f"{asset_type:<24} {count}")
            item.setData(Qt.ItemDataRole.UserRole, asset_type)
            self._type_summary.addItem(item)


def main(argv: list[str] | None = None) -> int:
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = BundleExplorerWindow()
    window.show()
    args = argv or []
    if args:
        window.bundleOpen(Path(args[0]))
    return int(app.exec())


def _sortValue(asset: AssetInfo, column: int) -> str | int:
    values: tuple[str | int, ...] = (
        asset.path_id,
        asset.asset_name or "",
        asset.asset_type,
        asset.container_path or "",
        asset.serialized_size if asset.serialized_size is not None else -1,
        len(asset.dependencies) + len(asset.external_references),
    )
    return values[column]


def _typeCounts(assets: Sequence[AssetInfo]) -> tuple[tuple[str, int], ...]:
    counts = Counter(asset.asset_type for asset in assets)
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold())))


def _bundleText(info: BundleInfo) -> str:
    return "\n".join(
        (
            f"File: {info.file_name}",
            f"Path: {info.path}",
            f"Size: {info.size}",
            f"Signature: {info.signature}",
            f"Unity version: {info.unity_version or 'unknown'}",
            f"Asset count: {info.asset_count}",
            f"External references: {len(info.external_references)}",
        )
    )


def _metadataText(asset: AssetInfo) -> str:
    return "\n".join(
        (
            f"Path ID: {asset.path_id}",
            f"Name: {asset.asset_name or 'unknown'}",
            f"Type: {asset.asset_type}",
            f"Container: {asset.container_path or 'unknown'}",
            f"Serialized size: {asset.serialized_size if asset.serialized_size is not None else 'unknown'}",
            f"References: {len(asset.dependencies) + len(asset.external_references)}",
        )
    )


if __name__ == "__main__":
    sys.exit(main())
