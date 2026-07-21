# FM26 FMF Reverse Engineering Notes

This document records discoveries about Football Manager 2026 tactic (`.fmf`) files.
Every known field should include confidence, evidence, sample files, and notes.

## Known Structures

| Offset | Meaning | Confidence | Evidence | Samples | Notes |
| --- | --- | --- | --- | --- | --- |
| `0x00` | Possible format/version byte `0x02` | Low | Observed in local samples | Pending curated samples | Needs comparison across many saves. |
| `0x01` | Possible format/version byte `0x01` | Low | Observed in local samples | Pending curated samples | Exposed as `2.1` only as a convenience label. |
| `0x02` | ASCII-like sequence `61 66 65 2e` (`afe.`) | Low | Observed prefix | Pending curated samples | May be magic, container marker, or coincidental payload. |

## Unknown Structures

Unknown fields are deliberately retained in reports and parser output. Do not discard bytes just
because they do not yet map to a tactical concept.

## Evidence Workflow

1. Create paired sample files where exactly one tactical setting changes.
2. Run `fmparser --tactic old.fmf --compare new.fmf`.
3. Record changed offsets, grouped changes, and whether checksums or compressed blocks also changed.
4. Repeat until the same offset reliably maps to one setting.
5. Promote the field to a typed parser structure only after repeatable evidence exists.

## Sample Naming

Place curated experiments in `samples/`:

- `sample01-balanced.fmf`
- `sample02-positive.fmf`
- `sample03-higher-tempo.fmf`
- `sample04-lower-tempo.fmf`
- `sample05-4-2-3-1.fmf`
- `sample06-4-3-3.fmf`
