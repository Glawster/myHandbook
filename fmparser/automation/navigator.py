"""High-level mouse and keyboard navigation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol, cast

from fmparser.automation.action import Action
from fmparser.automation.recorder import Recorder
from fmparser.automation.screen_map import ScreenMap
from fmparser.automation.screenshot import ScreenshotManager
from fmparser.automation.templateMatcher import Match, TemplateMatcher


class InputBackend(Protocol):
    def moveTo(self, x: int, y: int, duration: float = 0) -> None: ...
    def click(self, x: int, y: int, clicks: int = 1, button: str = "left") -> None: ...
    def hotkey(self, *keys: str) -> None: ...


class Navigator:
    def __init__(
        self,
        screen_map: ScreenMap,
        *,
        backend: InputBackend | None = None,
        screenshots: ScreenshotManager | None = None,
        matcher: TemplateMatcher | None = None,
        recorder: Recorder | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        if backend is None:
            import pyautogui

            backend = cast(InputBackend, pyautogui)
        self.screen_map = screen_map
        self.backend: InputBackend = backend
        self.screenshots = screenshots or ScreenshotManager(backend=backend)  # type: ignore[arg-type]
        self.matcher = matcher or TemplateMatcher(self.screenshots)
        self.recorder = recorder
        self.logger = logger or logging.getLogger(__name__)

    def move(self, target: str, *, duration: float = 0.0, record: bool = True) -> None:
        point = self.screen_map.get(target)
        self.backend.moveTo(point.x, point.y, duration=duration)
        self.logger.info("Moved pointer to %s (%d, %d)", target, point.x, point.y)
        self._record(Action("move", target, {"duration": duration}), record)

    def click(
        self, target: str, *, button: str = "left", clicks: int = 1, record: bool = True
    ) -> None:
        point = self.screen_map.get(target)
        self.backend.click(point.x, point.y, clicks=clicks, button=button)
        self.logger.info("Clicked %s at (%d, %d)", target, point.x, point.y)
        self._record(Action("click", target, {"button": button, "clicks": clicks}), record)

    def shortcut(self, *keys: str, record: bool = True) -> None:
        if not keys:
            raise ValueError("At least one shortcut key is required")
        self.backend.hotkey(*keys)
        self.logger.info("Pressed shortcut %s", "+".join(keys))
        self._record(Action("shortcut", parameters={"keys": list(keys)}), record)

    def imageWait(
        self,
        template: str | Path,
        *,
        timeout: float = 10.0,
        interval: float = 0.25,
        confidence: float = 0.9,
        record: bool = True,
    ) -> Match:
        """Wait for an image and optionally record the action."""
        match = self.matcher.imageWait(
            template, timeout=timeout, interval=interval, confidence=confidence
        )
        self._record(
            Action(
                "wait_for_image",
                str(template),
                {"timeout": timeout, "interval": interval, "confidence": confidence},
            ),
            record,
        )
        return match

    def capture(self, *, name: str | None = None, record: bool = True) -> Path:
        path = self.screenshots.save(name=name)
        self._record(Action("screenshot", parameters={"name": name}), record)
        return path

    def execute(self, action: Action, *, record: bool = True) -> Any:
        params = dict(action.parameters)
        if action.kind == "move" and action.target:
            return self.move(action.target, record=record, **params)
        if action.kind == "click" and action.target:
            return self.click(action.target, record=record, **params)
        if action.kind == "shortcut":
            return self.shortcut(*params.pop("keys", []), record=record, **params)
        if action.kind == "wait_for_image" and action.target:
            return self.imageWait(action.target, record=record, **params)
        if action.kind == "screenshot":
            return self.capture(record=record, **params)
        raise ValueError(f"Action {action.kind!r} requires a target")

    def _record(self, action: Action, enabled: bool) -> None:
        if enabled and self.recorder is not None:
            self.recorder.record(action)
