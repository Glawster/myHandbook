"""Command line interface for the FMF reverse engineering toolkit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from organiseMyProjects.logUtils import getLogger, setApplication

thisApplication = "myHandbook"
setApplication(thisApplication)
logger = getLogger(includeConsole=False)

from fmparser.diff import diff_files  # noqa: E402
from fmparser.bundleFilter import filter_assets  # noqa: E402
from fmparser.bundles import BundleError, UnityPyBundleReader  # noqa: E402
from fmparser.parser import FMFTactic, FMFParser  # noqa: E402
from fmparser.report import diff_report, inspection_report, structures_report  # noqa: E402
from fmparser.signatures import ascii_strings  # noqa: E402
from fmparser.structures import AssetData, AssetInfo, BundleInfo  # noqa: E402
from fmparser.structures_discovery import repeated_structures  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fmparser")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument(
        "-y",
        "--confirm",
        dest="confirm",
        action="store_true",
        help="execute changes (default is dry-run)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect", help="Inspect file signatures and sections")
    inspect.add_argument("file", type=Path)

    diff = subparsers.add_parser("diff", help="Compare two controlled tactic files")
    diff.add_argument("old", type=Path)
    diff.add_argument("new", type=Path)

    report = subparsers.add_parser("report", help="Generate a Markdown tactic report")
    report.add_argument("file", type=Path)

    dump = subparsers.add_parser("dump", help="Dump current parsed tactic model")
    dump.add_argument("file", type=Path)

    strings = subparsers.add_parser("strings", help="Extract printable ASCII strings")
    strings.add_argument("file", type=Path)
    strings.add_argument("--minimum", type=int, default=4)

    hex_view = subparsers.add_parser("hex", help="Print a compact hex view")
    hex_view.add_argument("file", type=Path)
    hex_view.add_argument("--offset", type=int, default=0)
    hex_view.add_argument("--length", type=int, default=256)

    structures = subparsers.add_parser("structures", help="Find repeated binary structures")
    structures.add_argument("file", type=Path)

    bundle = subparsers.add_parser("bundle", help="Inspect a Unity skin bundle")
    bundle_subparsers = bundle.add_subparsers(dest="bundle_command", required=True)

    bundle_list = bundle_subparsers.add_parser("list", help="List assets in one bundle")
    bundle_list.add_argument("file", type=Path)
    bundle_list.add_argument("--filter", default="", help="Filter by name, type, container, or path ID")
    bundle_list.add_argument("--type", default="", help="Filter by Unity object type")
    bundle_list.add_argument("--limit", type=int, default=100)

    bundle_preview = bundle_subparsers.add_parser("preview", help="Preview one readable asset")
    bundle_preview.add_argument("file", type=Path)
    bundle_preview.add_argument("asset_id", type=int)

    bundle_gui = bundle_subparsers.add_parser("gui", help="Launch the Qt bundle explorer prototype")
    bundle_gui.add_argument("file", type=Path, nargs="?")

    return parser


def main(argv: list[str] | None = None) -> int:
    global logger

    args = build_parser().parse_args(argv)
    dryRun = not args.confirm
    logger = getLogger(includeConsole=args.verbose > 0, dryRun=dryRun)
    logger.doing("fmparser command")
    logger.value("command", args.command)
    logger.value("dryRun", dryRun)

    try:
        if args.command == "inspect":
            filePath = pathValidateFile(args.file)
            print(inspection_report(FMFParser().inspect(filePath)), end="")
            logger.done("fmparser command")
            return 0
        if args.command == "diff":
            oldPath = pathValidateFile(args.old)
            newPath = pathValidateFile(args.new)
            print(diff_report(oldPath, newPath, diff_files(oldPath, newPath)), end="")
            logger.done("fmparser command")
            return 0
        if args.command == "report":
            tactic = FMFTactic.read(pathValidateFile(args.file))
            print(_tactic_report(tactic), end="")
            logger.done("fmparser command")
            return 0
        if args.command == "dump":
            print(FMFTactic.read(pathValidateFile(args.file)))
            logger.done("fmparser command")
            return 0
        if args.command == "strings":
            filePath = pathValidateFile(args.file)
            for item in ascii_strings(filePath.read_bytes(), minimum=args.minimum):
                print(f"{item.offset}: {item.value}")
            logger.done("fmparser command")
            return 0
        if args.command == "hex":
            filePath = pathValidateFile(args.file)
            print(_hex(filePath.read_bytes(), offset=args.offset, length=args.length), end="")
            logger.done("fmparser command")
            return 0
        if args.command == "structures":
            filePath = pathValidateFile(args.file)
            print(structures_report(repeated_structures(filePath.read_bytes())), end="")
            logger.done("fmparser command")
            return 0
        if args.command == "bundle":
            if args.bundle_command == "gui":
                from fmparser.qt_bundle_explorer import main as qt_main

                return qt_main([str(args.file)] if args.file else [])

            filePath = pathValidateFile(args.file)
            reader = UnityPyBundleReader()
            info = reader.open(filePath)
            if args.bundle_command == "list":
                assets = filter_assets(reader.list_assets(), text=args.filter, asset_type=args.type)
                print(_bundle_list_report(info, assets[: max(0, args.limit)]), end="")
                logger.done("fmparser command")
                return 0
            if args.bundle_command == "preview":
                print(_asset_data_report(reader.read_asset(args.asset_id)), end="")
                logger.done("fmparser command")
                return 0
    except BundleError as error:
        logger.error("bundle command failed: %s", error)
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        logger.error("fmparser command failed: %s", error)
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 2


def pathValidateFile(filePath: Path) -> Path:
    """Resolve and validate an input file path before processing."""
    resolvedPath = filePath.expanduser().resolve()
    if not resolvedPath.is_file():
        raise FileNotFoundError(f"Input file does not exist: {resolvedPath}")
    return resolvedPath


def _hex(data: bytes, *, offset: int, length: int) -> str:
    if offset < 0:
        raise ValueError("offset must be non-negative")
    if length < 0:
        raise ValueError("length must be non-negative")

    lines: list[str] = []
    stopOffset = min(len(data), offset + length)
    for row_offset in range(offset, stopOffset, 16):
        row = data[row_offset : min(row_offset + 16, stopOffset)]
        hex_bytes = " ".join(f"{byte:02x}" for byte in row)
        ascii_bytes = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in row)
        lines.append(f"{row_offset:08x}  {hex_bytes:<47}  {ascii_bytes}")
    return "\n".join(lines) + ("\n" if lines else "")


def _tactic_report(tactic: FMFTactic) -> str:
    lines = [
        "Formation",
        "---------",
        tactic.formation or "unknown",
        "",
        "Mentality",
        "---------",
        tactic.mentality or "unknown",
        "",
        "Roles",
        "-----",
    ]
    if tactic.players:
        lines.extend(
            f"{player.position}: {player.role or 'unknown'} ({player.duty or 'unknown'})"
            for player in tactic.players
        )
    else:
        lines.append("unknown")
    lines.extend(["", "Instructions", "------------"])
    lines.extend(tactic.team_instructions or ["unknown"])
    return "\n".join(lines) + "\n"


def _bundle_list_report(info: BundleInfo, assets: tuple[AssetInfo, ...]) -> str:
    lines = [
        "Bundle",
        "------",
        f"Filename: {info.file_name}",
        f"Path: {info.path}",
        f"Size: {info.size}",
        f"Signature: {info.signature}",
        f"Unity version: {info.unity_version or 'unknown'}",
        f"Asset count: {info.asset_count}",
        "",
        "Assets",
        "------",
    ]
    if not assets:
        lines.append("- none")
    for asset in assets:
        lines.append(
            f"- {asset.path_id}: {asset.asset_name or '(unnamed)'} "
            f"[{asset.asset_type}] container={asset.container_path or 'unknown'} "
            f"size={asset.serialized_size if asset.serialized_size is not None else 'unknown'} "
            f"refs={len(asset.dependencies) + len(asset.external_references)}"
        )
    return "\n".join(lines) + "\n"


def _asset_data_report(data: AssetData) -> str:
    lines = [
        "Asset",
        "-----",
        f"Path ID: {data.asset.path_id}",
        f"Name: {data.asset.asset_name or 'unknown'}",
        f"Type: {data.asset.asset_type}",
        f"Container: {data.asset.container_path or 'unknown'}",
        f"Representation: {data.representation}",
    ]
    if data.message:
        lines.extend(["", "Note", "----", data.message])
    if data.text:
        lines.extend(["", "Preview", "-------", data.text])
    elif not data.message:
        lines.extend(["", "Preview", "-------", "No readable preview is available."])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
