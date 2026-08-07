"""Batch orchestration for walking football session documents."""

from dataclasses import dataclass
from pathlib import Path

from scripts.builderErrors import SessionBuilderError, SessionDataError
from scripts.sessionBuilder import sessionBuild
from scripts.sessionParser import sessionParse


@dataclass(frozen=True)
class BuildSummary:
    """Counts produced by a batch session build."""

    discovered: int
    built: int
    failed: int


## build


def sessionsBuild(
    template: Path,
    sourceDirectory: Path,
    outputDirectory: Path,
    *,
    dryRun: bool,
) -> BuildSummary:
    """Validate and optionally build every YAML file in a directory."""
    _directoriesValidate(sourceDirectory, outputDirectory)
    sources = sorted((*sourceDirectory.glob("*.yaml"), *sourceDirectory.glob("*.yml")))
    if not sources:
        raise SessionDataError(f"no YAML session files found in: {sourceDirectory}")

    built = 0
    failed = 0
    outputNames: set[str] = set()
    for source in sources:
        try:
            session = sessionParse(source)
            outputName = f"{source.stem}.odt"
            if outputName.casefold() in outputNames:
                raise SessionDataError(f"duplicate output name: {outputName}")
            outputNames.add(outputName.casefold())
            if not dryRun:
                sessionBuild(template, session, outputDirectory / outputName)
            built += 1
        except SessionBuilderError:
            failed += 1
            raise
    return BuildSummary(discovered=len(sources), built=built, failed=failed)


## validation


def _directoriesValidate(sourceDirectory: Path, outputDirectory: Path) -> None:
    if not sourceDirectory.is_dir():
        raise SessionDataError(f"session directory does not exist: {sourceDirectory}")
    sourceResolved = sourceDirectory.resolve()
    outputResolved = outputDirectory.resolve()
    if outputResolved == sourceResolved or sourceResolved in outputResolved.parents:
        raise SessionDataError("generated output must not be inside the YAML source directory")
