"""Reusable desktop automation primitives for FMParser."""

from fmparser.automation.action import Action
from fmparser.automation.navigator import Navigator
from fmparser.automation.recorder import Recorder
from fmparser.automation.screen_map import Point, ScreenMap
from fmparser.automation.screenshot import ScreenshotManager
from fmparser.automation.template_matcher import Match, TemplateMatcher

__all__ = [
    "Action",
    "Match",
    "Navigator",
    "Point",
    "Recorder",
    "ScreenMap",
    "ScreenshotManager",
    "TemplateMatcher",
]
