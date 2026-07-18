# FMParser automation framework

This package contains desktop automation primitives only. It has no Football Manager workflows or
domain logic.

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

screen_map = ScreenMap.from_yaml("screen-map.yaml")
recorder = Recorder()
navigator = Navigator(screen_map, recorder=recorder)

recorder.start()
navigator.move("primary_button", duration=0.2)
navigator.click("primary_button")
navigator.shortcut("ctrl", "s")
navigator.wait_for_image("templates/confirmation.png", timeout=5)
navigator.capture(name="confirmation.png")
recorder.stop()
recorder.save_yaml("recordings/example.yaml")
```

PyAutoGUI uses the active Linux desktop session. On Wayland, desktop security policy may restrict
global input or screen capture; use an X11/XWayland session or grant the relevant portal permissions.
PyAutoGUI's fail-safe remains enabled by default: moving the pointer to a screen corner aborts a run.
