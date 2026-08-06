#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from organiseMyProjects.logUtils import getLogger, setApplication
from PIL import Image

# -----------------------------------------------------
# Football Manager Face Pack Updater
# -----------------------------------------------------

thisApplication = "organiseMyFooty"
setApplication(thisApplication)
logger = getLogger(includeConsole=False)

downloadsDir = Path.home() / "Downloads"
imageSize = (250, 250)
userConfigFile = Path.home() / ".config" / thisApplication / "config.json"
supportedExtensions = {
    ".png",
}
pngSourceExtensions = {
    ".jpg",
    ".jpeg",
}


## cli


def buildParser() -> argparse.ArgumentParser:
    """Build the command line parser for the face pack updater."""
    parser = argparse.ArgumentParser(
        description="Prepare Football Manager face images and update config.xml mappings."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="folder containing face images and config.xml; overrides user config",
    )
    parser.add_argument(
        "-y",
        "--confirm",
        dest="confirm",
        action="store_true",
        help="execute changes (default is dry-run)",
    )
    parser.add_argument(
        "--crop",
        action="store_true",
        help="center-crop PNG files to 250x250 before mapping them",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="create missing PNG files from numeric JPG files before copying and mapping",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the face pack update workflow."""
    global logger

    parser = buildParser()
    args = parser.parse_args(argv)
    dryRun = not args.confirm

    logger = getLogger(includeConsole=True, dryRun=dryRun)
    logger.doing("face pack update")

    try:
        sourceDir = sourceResolve(args.source)
        logger.value("sourceDir", sourceDir)
        logger.value("downloadsDir", downloadsDir)
        logger.value("crop", args.crop)
        logger.value("png", args.png)
        logger.value("dryRun", dryRun)

        if args.source is not None:
            userConfigSave({"source": str(sourceDir)})

        summary = workflowRun(sourceDir, crop=args.crop, png=args.png, dryRun=dryRun)
    except Exception as error:
        logger.error("face pack update failed: %s", error)
        print(f"Error: {error}", file=sys.stderr)
        return 1

    summaryPrint(summary, dryRun=dryRun, sourceDir=sourceDir)
    logger.done("face pack update")
    return 0


## workflow


def workflowRun(sourceDir: Path, *, crop: bool, png: bool, dryRun: bool) -> dict[str, int]:
    """Copy and map Football Manager PNG face images, optionally cropping them."""
    configFile = sourceDir / "config.xml"
    tree, maps = configLoad(configFile)
    existingIds = mappingsReadIds(maps)

    downloadImages, downloadPngCount = downloadsFindImages(downloadsDir, png=png, dryRun=dryRun)
    sourceImages, skippedCount, sourcePngCount = sourceFindImages(sourceDir, png=png, dryRun=dryRun)

    copiedCount = 0
    pngCount = downloadPngCount + sourcePngCount
    processedImages = [*sourceImages]

    for downloadFile in downloadImages:
        copiedImage = sourceDir / downloadFile.name
        if sourceHasImage(sourceDir, downloadFile):
            logger.info("download already exists in source: %s", copiedImage.name)
        else:
            downloadsCopyImage(downloadFile, copiedImage, dryRun=dryRun)
            copiedCount += 1
            processedImages.append(copiedImage)

    addedCount = 0
    updatedCount = 0

    for imageFile in processedImages:
        playerId = imageFile.stem

        if crop:
            imageCrop(imageFile, imageFile, dryRun=dryRun)
            updatedCount += 1

        if playerId in existingIds:
            continue

        mappingsAdd(maps, playerId, dryRun=dryRun)
        existingIds.add(playerId)
        addedCount += 1

    if copiedCount > 0 or updatedCount > 0 or addedCount > 0:
        configSave(tree, configFile, dryRun=dryRun)
    else:
        logger.info("no file changes required")

    return {
        "addedCount": addedCount,
        "copiedCount": copiedCount,
        "existingCount": len(existingIds),
        "pngCount": pngCount,
        "skippedCount": skippedCount,
        "updatedCount": updatedCount,
    }


## config


def configLoad(configFile: Path) -> tuple[ET.ElementTree, ET.Element]:
    """Load config.xml, or create the default config tree when missing."""
    if configFile.exists():
        tree = ET.parse(configFile)
        root = tree.getroot()
        maps = root.find("./list[@id='maps']")

        if maps is None:
            raise RuntimeError("Unable to locate <list id='maps'> in config.xml")

        return tree, maps

    root = ET.Element("record")

    ET.SubElement(
        root,
        "boolean",
        id="preload",
        value="false",
    )

    ET.SubElement(
        root,
        "boolean",
        id="amap",
        value="false",
    )

    maps = ET.SubElement(
        root,
        "list",
        id="maps",
    )

    return ET.ElementTree(root), maps


def configSave(tree: ET.ElementTree, configFile: Path, *, dryRun: bool) -> None:
    """Write the face pack config unless running in dry-run mode."""
    logActionPath("write config", configFile)
    if dryRun:
        return

    ET.indent(tree, space="    ")
    tree.write(
        configFile,
        encoding="UTF-8",
        xml_declaration=True,
    )
    logger.done("write config")


## userConfig


def userConfigLoad() -> dict[str, object]:
    """Load default values from the user JSON state file."""
    if not userConfigFile.exists():
        return {}

    with userConfigFile.open(encoding="UTF-8") as configHandle:
        values = json.load(configHandle)

    if not isinstance(values, dict):
        raise RuntimeError(f"User config must contain a JSON object: {userConfigFile}")

    return values


def userConfigSave(values: dict[str, object]) -> None:
    """Save default values to the user JSON state file."""
    currentValues = userConfigLoad()
    currentValues.update(values)

    logger.info("write user config: %s", userConfigFile)

    userConfigFile.parent.mkdir(parents=True, exist_ok=True)
    with userConfigFile.open("w", encoding="UTF-8") as configHandle:
        json.dump(currentValues, configHandle, indent=2)
        configHandle.write("\n")

    logger.info("wrote user config")


## downloads


def downloadsCopyImage(downloadFile: Path, destination: Path, *, dryRun: bool) -> None:
    """Copy a downloaded image into the source folder."""
    logActionPaths("copy downloaded image", downloadFile, destination)
    if dryRun:
        return

    shutil.copy2(downloadFile, destination)


def downloadsFindImages(sourceDir: Path, *, png: bool, dryRun: bool) -> tuple[list[Path], int]:
    """Find numeric Football Manager image files in the downloads folder."""
    if not sourceDir.is_dir():
        logger.info("downloads folder not found: %s", sourceDir)
        return [], 0

    sourceImages, _, pngCount = sourceFindImages(sourceDir, png=png, dryRun=dryRun)

    return sourceImages, pngCount


## images


def imageCrop(imageFile: Path, pngFile: Path, *, dryRun: bool) -> None:
    """Center-crop an image into a 250x250 PNG."""
    logActionPaths("crop image", imageFile, pngFile)
    if dryRun:
        return

    with Image.open(imageFile) as image:
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        width, height = image.size
        cropWidth = min(width, imageSize[0])
        cropHeight = min(height, imageSize[1])
        left = (width - cropWidth) // 2
        top = (height - cropHeight) // 2
        cropped = image.crop((left, top, left + cropWidth, top + cropHeight))

        if cropped.size != imageSize:
            output = Image.new("RGBA", imageSize, (0, 0, 0, 0))
            pasteLeft = (imageSize[0] - cropped.width) // 2
            pasteTop = (imageSize[1] - cropped.height) // 2
            output.paste(cropped, (pasteLeft, pasteTop))
            cropped = output

        cropped.save(pngFile)


def imageCreatePng(imageFile: Path, pngFile: Path, *, dryRun: bool) -> None:
    """Create a PNG copy of a source image."""
    logActionPaths("create png", imageFile, pngFile)
    if dryRun:
        return

    with Image.open(imageFile) as image:
        image.save(pngFile)


## mappings


def mappingsAdd(maps: ET.Element, playerId: str, *, dryRun: bool) -> None:
    """Add a player face mapping to the config map list."""
    logger.action("add mapping: %s", playerId)
    if dryRun:
        return

    ET.SubElement(
        maps,
        "record",
        attrib={
            "from": playerId,
            "to": f"graphics/pictures/person/{playerId}/portrait",
        },
    )


def mappingsReadIds(maps: ET.Element) -> set[str]:
    """Read existing mapped player IDs from the config map list."""
    return {
        record.attrib["from"]
        for record in maps.findall("record")
        if "from" in record.attrib
    }


## logs


def logActionPath(actionName: str, path: Path) -> None:
    """Log a dry-run-aware action with one path on a separate line."""
    logger.action(actionName)
    logger.multiline([f"path: {path}"])


def logActionPaths(actionName: str, source: Path, destination: Path) -> None:
    """Log a dry-run-aware action with source and destination paths."""
    logger.action(actionName)
    logger.multiline(
        [
            f"from: {source}",
            f"to:   {destination}",
        ]
    )


## paths


def pathValidateDirectory(sourceDir: Path) -> Path:
    """Resolve and validate a required source directory path."""
    resolvedDir = sourceDir.expanduser().resolve()

    if not resolvedDir.is_dir():
        raise FileNotFoundError(f"Source folder does not exist: {resolvedDir}")

    return resolvedDir


## source


def sourceFindImages(sourceDir: Path, *, png: bool, dryRun: bool) -> tuple[list[Path], int, int]:
    """Find numeric source images."""
    skippedCount = 0
    pngCount = 0
    imagesById: dict[str, Path] = {}

    for imageFile in sorted(sourceDir.iterdir()):
        fileSuffix = imageFile.suffix.lower()
        if fileSuffix not in supportedExtensions and not (png and fileSuffix in pngSourceExtensions):
            continue

        playerId = imageFile.stem
        if not playerId.isdigit():
            logger.info("skipping non-player image: %s", imageFile.name)
            skippedCount += 1
            continue

        if fileSuffix in supportedExtensions:
            imagesById.setdefault(playerId, imageFile)
            continue

        pngFile = imageFile.with_suffix(".png")
        if not pngFile.exists():
            imageCreatePng(imageFile, pngFile, dryRun=dryRun)
            pngCount += 1

        imagesById.setdefault(playerId, pngFile)

    return list(imagesById.values()), skippedCount, pngCount


def sourceHasImage(sourceDir: Path, imageFile: Path) -> bool:
    """Return whether the source folder already has this player image."""
    return (sourceDir / imageFile.name).exists()


def sourceResolve(sourceArg: Path | None) -> Path:
    """Resolve the source folder from CLI, user config, or script folder default."""
    if sourceArg is not None:
        return pathValidateDirectory(sourceArg)

    configValues = userConfigLoad()
    configuredSource = configValues.get("source")
    if configuredSource:
        if not isinstance(configuredSource, str):
            raise RuntimeError("User config value 'source' must be a string")
        return pathValidateDirectory(Path(configuredSource))

    return pathValidateDirectory(Path(__file__).parent)


## summary


def summaryPrint(summary: dict[str, int], *, dryRun: bool, sourceDir: Path) -> None:
    """Print the completion summary for the face pack update."""
    mode = "Dry Run" if dryRun else "Updated"

    print()
    print("----------------------------------------")
    print(f"Football Manager Face Pack {mode}")
    print("----------------------------------------")
    print(f"Source folder    : {sourceDir}")
    print(f"Downloads copied : {summary['copiedCount']}")
    print(f"PNGs created     : {summary['pngCount']}")
    print(f"Images updated   : {summary['updatedCount']}")
    print(f"New mappings     : {summary['addedCount']}")
    print(f"Skipped files    : {summary['skippedCount']}")
    print(f"Existing mappings: {summary['existingCount']}")
    print()


if __name__ == "__main__":
    sys.exit(main())
