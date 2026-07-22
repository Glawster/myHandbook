# FMParser Automation Framework

The automation package contains reusable desktop automation primitives. Apart from the explicitly
documented capture plugin below, it has no Football Manager workflows or domain logic.

Install FMParser with the automation dependencies on Python 3.12 or newer:

```bash
python3.12 -m pip install -e '.[automation,dev]'
```

Coordinates are read from YAML and refer to the host desktop. This works for native Linux windows
and Windows applications displayed through Proton because input and screenshots are handled by the
Linux desktop:

```yaml
coordinates:
  primary_button: {x: 800, y: 600}
  toolbar_item: [120, 45]
```

```python
from fmparser.automation import Navigator, Recorder, ScreenMap

screenMap = ScreenMap.from_yaml("screen-map.yaml")
recorder = Recorder()
navigator = Navigator(screenMap, recorder=recorder)

recorder.start()
navigator.move("primary_button", duration=0.2)
navigator.click("primary_button")
navigator.shortcut("ctrl", "s")
navigator.wait_for_image("templates/confirmation.png", timeout=5)
navigator.capture(name="confirmation.png")
recorder.stop()
recorder.save_yaml("output/recordings/example.yaml")
```

Screenshots are written under `output/screenshots/` by default. PyAutoGUI uses the active Linux
desktop session. On Wayland, desktop security policy may restrict global input or screen capture;
use an X11/XWayland session or grant the relevant portal permissions. PyAutoGUI's fail-safe remains
enabled by default: moving the pointer to a screen corner aborts a run.

## Striker IP role capture plugin

The only Football Manager-specific workflow currently provided is
`TacticsIPRoleCapturePlugin`. Copy
`fmparser/automation/plugins/tactics_ip_role.screen-map.example.yaml`, replace the placeholder
coordinates, and run it with a navigator:

```python
from fmparser.automation import Navigator, ScreenMap
from fmparser.automation.plugins import TacticsIPRoleCapturePlugin

screenMap = ScreenMap.from_yaml("tactics_ip_role.screen-map.yaml")
plugin = TacticsIPRoleCapturePlugin(Navigator(screenMap))
result = plugin.tacticsCapture()
```

It performs only this sequence: open Tactics, select Striker, open the IP role, capture a
screenshot, open Instructions, and capture a second screenshot.
