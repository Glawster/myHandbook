"""Shared pytest configuration for the session builder."""

import sys
from pathlib import Path

APPLICATION_DIRECTORY = Path(__file__).parents[1]
sys.path.insert(0, str(APPLICATION_DIRECTORY))
