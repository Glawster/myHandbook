"""Serializable automation actions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ActionKind = Literal["move", "click", "shortcut", "wait_for_image", "screenshot"]


@dataclass(frozen=True, slots=True)
class Action:
    """A single backend-independent automation instruction."""

    kind: ActionKind
    target: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Action:
        kind = value.get("kind")
        valid = {"move", "click", "shortcut", "wait_for_image", "screenshot"}
        if kind not in valid:
            raise ValueError(f"Unsupported action kind: {kind!r}")
        parameters = value.get("parameters", {})
        if not isinstance(parameters, Mapping):
            raise ValueError("Action parameters must be a mapping")
        target = value.get("target")
        if target is not None and not isinstance(target, str):
            raise ValueError("Action target must be a string or null")
        return cls(kind=kind, target=target, parameters=dict(parameters))
