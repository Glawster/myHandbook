"""Action recording, YAML persistence, and replay."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from PySide6.QtCore import QObject, Signal

from fmparser.automation.action import Action

if TYPE_CHECKING:
    from fmparser.automation.navigator import Navigator


class Recorder(QObject):
    action_recorded = Signal(object)
    recording_changed = Signal(bool)

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        super().__init__()
        self.actions: list[Action] = []
        self.is_recording = False
        self.logger = logger or logging.getLogger(__name__)

    def start(self, *, clear: bool = False) -> None:
        if clear:
            self.actions.clear()
        self.is_recording = True
        self.recording_changed.emit(True)

    def stop(self) -> tuple[Action, ...]:
        self.is_recording = False
        self.recording_changed.emit(False)
        return tuple(self.actions)

    def record(self, action: Action) -> None:
        if self.is_recording:
            self.actions.append(action)
            self.action_recorded.emit(action)
            self.logger.debug("Recorded %s action", action.kind)

    def yamlSave(self, path: str | Path) -> Path:
        """Save recorded actions to a YAML file."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as stream:
            yaml.safe_dump(
                {"actions": [action.dictionaryCreate() for action in self.actions]},
                stream,
                sort_keys=False,
            )
        return destination

    @classmethod
    def yamlLoad(cls, path: str | Path) -> Recorder:
        """Load and validate recorded actions from a YAML file."""
        with Path(path).open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
        if not isinstance(data, Mapping) or not isinstance(data.get("actions", []), list):
            raise ValueError("Recording YAML must contain an actions list")
        recorder = cls()
        recorder.actions = [Action.dictionaryLoad(value) for value in data.get("actions", [])]
        return recorder

    def replay(self, navigator: Navigator) -> None:
        for action in tuple(self.actions):
            navigator.execute(action, record=False)
