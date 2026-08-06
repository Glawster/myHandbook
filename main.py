#!/usr/bin/env python3
"""Root entry point for the handbook tooling."""

from __future__ import annotations

import sys
from pathlib import Path

from organiseMyProjects.logUtils import setApplication

thisApplication = Path(__file__).parent.name
setApplication(thisApplication)

from fmsat.main import main as fmsatMain  # noqa: E402


def main() -> int:
    """Run the default repository command line tool."""
    return fmsatMain()


if __name__ == "__main__":
    sys.exit(main())
