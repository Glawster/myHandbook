from pathlib import Path
from unittest.mock import Mock, call

from fmparser.automation.plugins import TacticsIPRoleCapturePlugin


def test_plugin_runs_only_the_requested_workflow() -> None:
    navigator = Mock()
    navigator.capture.side_effect = [
        Path("output/screenshots/striker_ip_role.png"),
        Path("output/screenshots/striker_ip_role_instructions.png"),
    ]
    plugin = TacticsIPRoleCapturePlugin(navigator)

    result = plugin.tacticsCapture()

    assert navigator.method_calls == [
        call.click("open_tactics"),
        call.click("striker"),
        call.click("ip_role"),
        call.capture(name="striker_ip_role.png"),
        call.click("instructions"),
        call.capture(name="striker_ip_role_instructions.png"),
    ]
    assert result.ipRole == Path("output/screenshots/striker_ip_role.png")
    assert result.instructions == Path("output/screenshots/striker_ip_role_instructions.png")
