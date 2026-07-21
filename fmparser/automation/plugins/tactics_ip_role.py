"""Capture the striker's IP role and instruction screens."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fmparser.automation.navigator import Navigator


@dataclass(frozen=True, slots=True)
class TacticsCaptureResult:
    """Paths produced by a tactics capture run."""

    ipRole: Path
    instructions: Path


class TacticsIPRoleCapturePlugin:
    """Run the single supported Football Manager automation workflow."""

    def __init__(self, navigator: Navigator) -> None:
        self.navigator = navigator

    ## tactics

    def tacticsCapture(self) -> TacticsCaptureResult:
        """Open the striker IP role and capture its role and instruction screens."""
        self.navigator.click("open_tactics")
        self.navigator.click("striker")
        self.navigator.click("ip_role")
        ipRole = self.navigator.capture(name="striker_ip_role.png")
        self.navigator.click("instructions")
        instructions = self.navigator.capture(name="striker_ip_role_instructions.png")

        return TacticsCaptureResult(ipRole=ipRole, instructions=instructions)
