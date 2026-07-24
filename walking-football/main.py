"""Command-line entry point for the walking football session builder."""

import argparse
import sys
from pathlib import Path
from typing import Sequence

from organiseMyProjects.logUtils import getLogger, setApplication

thisApplication = Path(__file__).parent.name
setApplication(thisApplication)
logger = getLogger(includeConsole=False)

from scripts.builderErrors import SessionBuilderError  # noqa: E402
from scripts.buildSessions import sessionsBuild  # noqa: E402


## CLI


def parserBuild() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    projectDirectory = Path(__file__).parent
    parser = argparse.ArgumentParser(
        description="Build formatted walking football session plans from YAML."
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=projectDirectory / "templates" / "sessionTemplate.odt",
        help="ODT template path",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=projectDirectory / "sessions",
        help="directory containing YAML session files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=projectDirectory / "generated",
        help="generated ODT directory",
    )
    parser.add_argument(
        "-y",
        "--confirm",
        dest="confirm",
        action="store_true",
        help="execute changes (default is dry-run)",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the session builder and return a process exit status."""
    global logger

    args = parserBuild().parse_args(arguments)
    dryRun = not args.confirm
    logger = getLogger(includeConsole=True, dryRun=dryRun)
    logger.doing("session build")
    try:
        summary = sessionsBuild(
            args.template,
            args.source,
            args.output,
            dryRun=dryRun,
        )
    except SessionBuilderError as error:
        logger.error(str(error))
        return 1

    logger.info(
        "discovered %s sessions, processed %s, failed %s",
        summary.discovered,
        summary.built,
        summary.failed,
    )
    logger.done("session build complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
