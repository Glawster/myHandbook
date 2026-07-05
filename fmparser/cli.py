"""Command line interface for the FMF reverse engineering toolkit."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from fmparser.diff import diff_files
from fmparser.parser import FMFTactic, FMFParser
from fmparser.report import diff_report, inspection_report, structures_report
from fmparser.signatures import ascii_strings
from fmparser.structures_discovery import repeated_structures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fmparser")
    parser.add_argument("-v", "--verbose", action="count", default=0)
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

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING - min(args.verbose, 2) * 10)

    if args.command == "inspect":
        print(inspection_report(FMFParser().inspect(args.file)), end="")
        return 0
    if args.command == "diff":
        print(diff_report(args.old, args.new, diff_files(args.old, args.new)), end="")
        return 0
    if args.command == "report":
        tactic = FMFTactic.read(args.file)
        print(_tactic_report(tactic), end="")
        return 0
    if args.command == "dump":
        print(FMFTactic.read(args.file))
        return 0
    if args.command == "strings":
        for item in ascii_strings(args.file.read_bytes(), minimum=args.minimum):
            print(f"{item.offset}: {item.value}")
        return 0
    if args.command == "hex":
        print(_hex(args.file.read_bytes(), offset=args.offset, length=args.length), end="")
        return 0
    if args.command == "structures":
        print(structures_report(repeated_structures(args.file.read_bytes())), end="")
        return 0
    return 2


def _hex(data: bytes, *, offset: int, length: int) -> str:
    lines: list[str] = []
    for row_offset in range(offset, min(len(data), offset + length), 16):
        row = data[row_offset : row_offset + 16]
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
        lines.extend(f"{player.position}: {player.role or 'unknown'} ({player.duty or 'unknown'})" for player in tactic.players)
    else:
        lines.append("unknown")
    lines.extend(["", "Instructions", "------------"])
    lines.extend(tactic.team_instructions or ["unknown"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
