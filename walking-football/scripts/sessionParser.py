"""YAML parsing and validation for walking football sessions."""

from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.builderErrors import SessionDataError
from scripts.sessionModels import Session

_REQUIRED_SCALARS = (
    "sessionNumber",
    "sessionTitle",
    "theme",
    "keyPhrase",
    "duration",
    "players",
)
_SEQUENCES = ("equipment", "objectives")
_OPTIONAL_SCALARS = (
    "warmup",
    "drill1",
    "drill2",
    "drill3",
    "matchPractice",
    "coolDown",
    "coachingPoints",
    "commonMistakes",
    "analysis",
    "sessionSummary",
    "nextSession",
)
_KNOWN_FIELDS = frozenset((*_REQUIRED_SCALARS, *_SEQUENCES, *_OPTIONAL_SCALARS))


## session


def sessionParse(path: Path) -> Session:
    """Read and validate one YAML session definition."""
    _pathValidate(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise SessionDataError(f"{path}: cannot read YAML: {error}") from error

    if not isinstance(raw, Mapping):
        raise SessionDataError(f"{path}: YAML root must be a mapping")

    data = dict(raw)
    _fieldsValidate(path, data)
    return Session(
        sessionNumber=_integerRead(path, data, "sessionNumber"),
        sessionTitle=_scalarRead(path, data, "sessionTitle"),
        theme=_scalarRead(path, data, "theme"),
        keyPhrase=_scalarRead(path, data, "keyPhrase"),
        duration=_scalarRead(path, data, "duration"),
        players=_scalarRead(path, data, "players"),
        equipment=_sequenceRead(path, data, "equipment"),
        objectives=_sequenceRead(path, data, "objectives"),
        **{name: _optionalScalarRead(path, data, name) for name in _OPTIONAL_SCALARS},
    )


## validation


def _fieldsValidate(path: Path, data: Mapping[str, Any]) -> None:
    unknown = sorted(set(data) - _KNOWN_FIELDS)
    if unknown:
        raise SessionDataError(f"{path}: unknown fields: {', '.join(unknown)}")

    missing = sorted(set((*_REQUIRED_SCALARS, *_SEQUENCES)) - set(data))
    if missing:
        raise SessionDataError(f"{path}: missing required fields: {', '.join(missing)}")


def _integerRead(path: Path, data: Mapping[str, Any], name: str) -> int:
    value = data[name]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SessionDataError(f"{path}: {name} must be a positive integer")
    return value


def _optionalScalarRead(path: Path, data: Mapping[str, Any], name: str) -> str:
    if name not in data:
        return ""
    return _scalarRead(path, data, name)


def _pathValidate(path: Path) -> None:
    if not path.is_file():
        raise SessionDataError(f"session file does not exist: {path}")
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise SessionDataError(f"session file must use .yaml or .yml: {path}")


def _scalarRead(path: Path, data: Mapping[str, Any], name: str) -> str:
    value = data[name]
    if not isinstance(value, str) or not value.strip():
        raise SessionDataError(f"{path}: {name} must be a non-empty string")
    return value.strip()


def _sequenceRead(path: Path, data: Mapping[str, Any], name: str) -> tuple[str, ...]:
    value = data[name]
    if not isinstance(value, list) or not value:
        raise SessionDataError(f"{path}: {name} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise SessionDataError(f"{path}: every {name} item must be a non-empty string")
    return tuple(item.strip() for item in value)
