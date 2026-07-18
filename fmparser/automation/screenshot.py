"""Desktop screenshot capture and persistence."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, cast

from PIL import Image


class ScreenshotBackend(Protocol):
    def screenshot(self, region: tuple[int, int, int, int] | None = None) -> Any: ...


class ScreenshotManager:
    def __init__(
        self,
        output_dir: str | Path = "screenshots",
        *,
        backend: ScreenshotBackend | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        if backend is None:
            import pyautogui

            backend = cast(ScreenshotBackend, pyautogui)
        self.output_dir = Path(output_dir)
        self.backend: ScreenshotBackend = backend
        self.logger = logger or logging.getLogger(__name__)

    def capture(self, region: tuple[int, int, int, int] | None = None) -> Image.Image:
        image = self.backend.screenshot(region=region)
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)
        self.logger.info("Captured screenshot%s", f" region={region}" if region else "")
        return image

    def save(
        self,
        image: Image.Image | None = None,
        *,
        name: str | None = None,
        region: tuple[int, int, int, int] | None = None,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = name or datetime.now().strftime("screenshot_%Y%m%d_%H%M%S_%f.png")
        path = self.output_dir / filename
        (image or self.capture(region)).save(path)
        self.logger.info("Saved screenshot to %s", path)
        return path
