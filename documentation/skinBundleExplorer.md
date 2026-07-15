# FM26 Skin Bundle Explorer

Football Manager 2026 skins can include Unity asset bundles such as
`ui-panelids-uxml_assets_all.bundle`, `ui-tableviews_assets_all.bundle`, and
`ui-widgets_assets_all.bundle`. These files may contain UI Toolkit layouts, table definitions,
widgets, styles, textures, sprites, and supporting Unity objects.

This tool is read-only. It is intended for inspection and understanding only.

## Installation

The existing FMF parser still has no required runtime dependencies. Bundle inspection uses optional
dependencies:

```bash
pip install ".[bundles]"
pip install ".[gui]"
```

Install both extras to use the Qt prototype:

```bash
pip install ".[bundles,gui]"
```

## Command Line Usage

List assets in one bundle:

```bash
fmparser bundle list /path/to/ui-widgets_assets_all.bundle
```

Filter by text or type:

```bash
fmparser bundle list /path/to/ui-widgets_assets_all.bundle --filter player --type VisualTreeAsset
```

Preview one safely readable asset:

```bash
fmparser bundle preview /path/to/ui-widgets_assets_all.bundle 123456789
```

Launch the Qt explorer:

```bash
fmparser bundle gui
fmparser bundle gui /path/to/ui-widgets_assets_all.bundle
```

## Qt Prototype

The Qt interface provides:

- Open Bundle and Close Bundle actions.
- A sortable asset table with path ID, name, type, container, size, and reference count.
- Text filtering across path ID, asset name, asset type, and container path.
- Type filtering.
- A metadata panel for the selected asset.
- A raw/textual preview panel where safe decoding is available.
- A diagnostic log panel and status bar.

Bundle opening and asset preview run in Qt worker tasks. The UI is updated only from the main
thread.

## Supported Inspection

The first milestone reports:

- file name;
- file size;
- bundle signature;
- Unity version when UnityPy exposes it;
- asset count;
- path ID;
- asset type;
- asset name where available;
- serialized size where available;
- container path where available;
- best-effort external reference information.

Text previews are attempted for `TextAsset`. Serialized Unity object data is attempted for
`VisualTreeAsset`, `MonoBehaviour`, stylesheets, and other objects when UnityPy can provide a type
tree. Reconstructed or serialized data is labelled as such and should not be treated as original
source UXML unless independent evidence proves that.

## Not Supported Yet

The first milestone does not:

- modify bundles;
- rebuild bundles;
- replace game assets;
- write into the FM26 installation;
- recursively extract every asset;
- build a persistent dependency database;
- convert the whole FMParser application to GUI.

Texture and sprite previews are reported as unsupported for now.

## Legal and Practical Notes

Do not commit proprietary Football Manager files, third-party skin bundles, or extracted assets to
this repository. Local `.bundle` files, `local-bundles/`, and `bundle-exports/` are ignored by Git.

FM26 installation paths are not assumed. Select a bundle manually or pass its path on the command
line.
