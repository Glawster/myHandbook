"""YAML-driven named screen coordinates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class Point:
    """An absolute desktop coordinate."""

    x: int
    y: int


class ScreenMap:
    """A validated map of symbolic names to absolute desktop coordinates."""

    def __init__(self, coordinates: Mapping[str, Point]) -> None:
        self._coordinates = dict(coordinates)

    @classmethod
    def yamlLoad(cls, path: str | Path) -> ScreenMap:
        """Load and validate named coordinates from a YAML file."""
        with Path(path).open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
        if not isinstance(data, Mapping):
            raise ValueError("Screen map YAML must contain a mapping")
        raw_coordinates = data.get("coordinates", data)
        if not isinstance(raw_coordinates, Mapping):
            raise ValueError("'coordinates' must be a mapping")
        return cls(
            {
                str(name): cls._parse_point(name, value)
                for name, value in raw_coordinates.items()
            }
        )

    @staticmethod
    def _parse_point(name: Any, value: Any) -> Point:
        if isinstance(value, Mapping):
            x, y = value.get("x"), value.get("y")
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            x, y = value
        else:
            raise ValueError(f"Coordinate {name!r} must contain x and y")
        if (
            not isinstance(x, int)
            or isinstance(x, bool)
            or not isinstance(y, int)
            or isinstance(y, bool)
        ):
            raise ValueError(f"Coordinate {name!r} values must be integers")
        if x < 0 or y < 0:
            raise ValueError(f"Coordinate {name!r} values must be non-negative")
        return Point(x, y)

    def get(self, name: str) -> Point:
        """Return a named coordinate or raise a descriptive error."""
        try:
            return self._coordinates[name]
        except KeyError as error:
            raise KeyError(f"Unknown screen coordinate: {name!r}") from error

    def __contains__(self, name: object) -> bool:
        return name in self._coordinates
