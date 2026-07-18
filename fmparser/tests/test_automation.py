from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image, ImageDraw

from fmparser.automation import (
    Action,
    Navigator,
    Point,
    Recorder,
    ScreenMap,
    ScreenshotManager,
    TemplateMatcher,
)


class FakeBackend:
    def __init__(self, image: Image.Image | None = None) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.image = image or Image.new("RGB", (30, 20), "black")

    def moveTo(self, x: int, y: int, duration: float = 0) -> None:
        self.calls.append(("move", x, y, duration))

    def click(self, x: int, y: int, clicks: int = 1, button: str = "left") -> None:
        self.calls.append(("click", x, y, clicks, button))

    def hotkey(self, *keys: str) -> None:
        self.calls.append(("hotkey", *keys))

    def screenshot(self, region: tuple[int, int, int, int] | None = None) -> Image.Image:
        self.calls.append(("screenshot", region))
        return self.image.copy()


def test_screen_map_loads_both_yaml_coordinate_styles(tmp_path: Path) -> None:
    path = tmp_path / "screen.yaml"
    path.write_text("coordinates:\n  menu: {x: 12, y: 34}\n  close: [90, 10]\n", encoding="utf-8")

    screen_map = ScreenMap.from_yaml(path)

    assert screen_map.get("menu") == Point(12, 34)
    assert screen_map.get("close") == Point(90, 10)
    assert "menu" in screen_map


@pytest.mark.parametrize(
    "yaml_text",
    ["coordinates: []", "coordinates: {bad: [1]}", "coordinates: {bad: {x: -1, y: 2}}"],
)
def test_screen_map_rejects_invalid_yaml(tmp_path: Path, yaml_text: str) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml_text, encoding="utf-8")

    with pytest.raises(ValueError):
        ScreenMap.from_yaml(path)


def test_navigator_dispatches_input_and_records_actions() -> None:
    backend = FakeBackend()
    recorder = Recorder()
    recorder.start()
    navigator = Navigator(ScreenMap({"button": Point(4, 8)}), backend=backend, recorder=recorder)

    navigator.move("button", duration=0.2)
    navigator.click("button", button="right", clicks=2)
    navigator.shortcut("ctrl", "s")

    assert backend.calls[:3] == [
        ("move", 4, 8, 0.2),
        ("click", 4, 8, 2, "right"),
        ("hotkey", "ctrl", "s"),
    ]
    assert [action.kind for action in recorder.stop()] == ["move", "click", "shortcut"]


def test_recorder_round_trip_and_replay(tmp_path: Path) -> None:
    recorder = Recorder()
    recorder.start()
    recorder.record(Action("click", "save", {"clicks": 1, "button": "left"}))
    recorder.record(Action("shortcut", parameters={"keys": ["ctrl", "q"]}))
    recorder.stop()
    path = recorder.save_yaml(tmp_path / "recording.yaml")

    loaded = Recorder.from_yaml(path)
    navigator = Mock()
    loaded.replay(navigator)

    assert loaded.actions == recorder.actions
    assert [call.args[0] for call in navigator.execute.call_args_list] == loaded.actions
    assert all(call.kwargs == {"record": False} for call in navigator.execute.call_args_list)


def test_screenshot_manager_captures_and_saves(tmp_path: Path) -> None:
    backend = FakeBackend(Image.new("RGB", (8, 6), "blue"))
    manager = ScreenshotManager(tmp_path, backend=backend)

    path = manager.save(name="capture.png", region=(1, 2, 3, 4))

    assert path == tmp_path / "capture.png"
    assert Image.open(path).size == (8, 6)
    assert backend.calls == [("screenshot", (1, 2, 3, 4))]


def test_template_matcher_finds_image_center() -> None:
    image = Image.fromarray(np.random.default_rng(2).integers(0, 255, (80, 100, 3), dtype=np.uint8))
    template = image.crop((23, 31, 43, 46))
    manager = ScreenshotManager(backend=FakeBackend(image))

    match = TemplateMatcher(manager).find(template, confidence=0.99)

    assert match is not None
    assert (match.x, match.y, match.width, match.height) == (23, 31, 20, 15)
    assert match.center == (33, 38)


def test_template_matcher_times_out() -> None:
    screen = Image.new("RGB", (20, 20), "black")
    template = Image.new("RGB", (5, 5), "black")
    ImageDraw.Draw(template).point((2, 2), fill="white")
    times = iter([0.0, 0.0, 0.0, 1.0, 1.0])
    matcher = TemplateMatcher(
        ScreenshotManager(backend=FakeBackend(screen)),
        clock=lambda: next(times),
        sleeper=lambda _: None,
    )

    with pytest.raises(TimeoutError):
        matcher.wait_for(template, timeout=1.0, interval=0.25)


def test_action_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        Action.from_dict({"kind": "launch"})
