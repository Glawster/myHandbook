# FMParser

`fmparser` is a Python 3.12+ reverse engineering toolkit for Football Manager tactic (`.fmf`)
files. It starts with careful binary inspection and differential analysis, then gives the project a
place to promote proven byte mappings into a real parser over time.

## Install

```bash
python -m pip install -e ".[dev]"
```

Optional compression probes:

```bash
python -m pip install -e ".[compression]"
```

## CLI

```bash
fmparser inspect tactic.fmf
fmparser diff old.fmf new.fmf
fmparser report tactic.fmf
fmparser dump tactic.fmf
fmparser strings tactic.fmf
fmparser hex tactic.fmf
fmparser structures tactic.fmf
```

Without installation, run:

```bash
python -m fmparser.cli inspect tactic.fmf
```

## Current Capabilities

- File size, SHA-256, header bytes, observed-prefix detection, and tentative flags.
- Entropy scans for likely compressed/encrypted blocks and likely structured/string-table areas.
- ASCII string extraction with offsets.
- Compression probes for zlib, gzip, lzma, raw deflate, and optional lz4/zstd.
- Binary reader supporting integers, floats, endianness, variable-length integers, seeking, and
  bookmarks.
- Differential analysis that groups changed bytes from controlled experiments.
- Repeated fixed-width structure discovery.
- Markdown reports.

## Architecture

```text
fmparser/
    __init__.py
    parser.py
    structures.py
    binary.py
    compression.py
    signatures.py
    report.py
    cli.py
    diff.py
    structures_discovery.py
tests/
samples/
docs/
```

## Reverse Engineering Discipline

The parser does not yet claim to extract formation, mentality, roles, duties, or instructions. Those
fields are intentionally nullable until controlled sample diffs prove their byte mappings.

Record discoveries in [`docs/reverse-engineering.md`](docs/reverse-engineering.md), including:

- offset
- meaning
- confidence
- evidence
- sample files used
- notes

Unknown structures should stay documented rather than discarded.
