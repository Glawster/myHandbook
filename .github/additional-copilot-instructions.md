# Additional Copilot Instructions for myHandbook

These instructions are repository-specific and extend the Python-first master rules in `.github/copilot-instructions.md`.

## Scope

- Keep Python application standards from the master file as the default for code changes.
- Use this file for repository structure and content conventions only.

## Repository Layout Conventions

- Chapter directories use zero-padded numeric prefixes when present, for example `01 - ...`, `05 - ...`.
- Keep handbook content grouped by domain at the top level (for example `football-manager/`, `walking-football/`, `linux/`).
- Place chapter content under each domain's `chapters/` directory.
- Keep reusable template assets in `templates/assets/`.
- Keep working scripts in `scripts/` and avoid committing runtime cache artifacts.

## Diagram and Document Conventions

- Mermaid source files use `.mmd` and should live with the relevant chapter content.
- Preserve existing naming conventions for chapter diagram files.
- Generated exports should not be committed unless there is an explicit requirement.

## Change Discipline

- Prefer moving/renaming existing files over delete-and-recreate when restructuring content.
- When changing structure, keep chapter numbering and path style consistent across all domains.
- Keep `.gitignore` aligned with generated artifacts introduced by scripts or export workflows.
