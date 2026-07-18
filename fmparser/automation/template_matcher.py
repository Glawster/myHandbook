"""OpenCV-based image matching with polling support."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from fmparser.automation.screenshot import ScreenshotManager


@dataclass(frozen=True, slots=True)
class Match:
    x: int
    y: int
    width: int
    height: int
    confidence: float

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2


class TemplateMatcher:
    def __init__(
        self,
        screenshots: ScreenshotManager,
        *,
        logger: logging.Logger | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.screenshots = screenshots
        self.logger = logger or logging.getLogger(__name__)
        self.clock = clock
        self.sleeper = sleeper

    def find(
        self, template: str | Path | Image.Image, *, confidence: float = 0.9
    ) -> Match | None:
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        screen = self._to_bgr(self.screenshots.capture())
        needle = self._load_template(template)
        height, width = needle.shape[:2]
        if height > screen.shape[0] or width > screen.shape[1]:
            return None
        scores = cv2.matchTemplate(screen, needle, cv2.TM_CCOEFF_NORMED)
        _, score, _, location = cv2.minMaxLoc(scores)
        if score < confidence:
            return None
        return Match(location[0], location[1], width, height, float(score))

    def wait_for(
        self,
        template: str | Path | Image.Image,
        *,
        timeout: float = 10.0,
        interval: float = 0.25,
        confidence: float = 0.9,
    ) -> Match:
        if timeout < 0 or interval <= 0:
            raise ValueError("timeout must be non-negative and interval must be positive")
        deadline = self.clock() + timeout
        while True:
            match = self.find(template, confidence=confidence)
            if match is not None:
                self.logger.info("Found template at %s", match.center)
                return match
            if self.clock() >= deadline:
                raise TimeoutError(f"Image was not found within {timeout:g} seconds")
            self.sleeper(min(interval, max(0.0, deadline - self.clock())))

    @classmethod
    def _load_template(cls, template: str | Path | Image.Image) -> np.ndarray:
        if isinstance(template, Image.Image):
            return cls._to_bgr(template)
        image = cv2.imread(str(template), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Unable to read template: {template}")
        return image

    @staticmethod
    def _to_bgr(image: Image.Image) -> np.ndarray:
        rgb = np.asarray(image.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
