# Poly Savi 8400 Office — Linux troubleshooting

Tested on Pop!_OS 22.04 with PipeWire, 18 November 2026.

## Symptom and confirmed fix

The headset announced **Base not connected**. Linux recognised both USB audio endpoints, but no sound was heard.

1. Disconnect power from the base station.
2. Wait approximately 15 seconds.
3. Reconnect power and allow the headset to reconnect.
4. Retest sound through the headset.

A base station power reset restored operation. No Linux restart, driver installation or audio configuration change was required. The precise cause of the lost DECT connection was not established.

## Check USB and audio detection

```bash
lsusb | grep -Ei 'poly|plantronics|savi|hp'
pactl list short sinks
pactl list short sources
```

Expected USB identification: `047f:ac37 Plantronics, Inc. Poly Savi 8400 Office Series`.

PipeWire exposed a mono playback sink at 48 kHz and mono microphone source at 16 kHz. `SUSPENDED` on an idle sink is normal; a monitor source is not the headset microphone.

## Test playback directly

Select the computer audio channel on the base and switch on the headset.

```bash
SAVI_SINK=$(pactl list short sinks | awk '/Poly_Savi/ {print $2; exit}')
paplay --device="$SAVI_SINK" /usr/share/sounds/freedesktop/stereo/complete.oga
```

For a continuous tone (stop with Ctrl+C):

```bash
PULSE_SINK="$SAVI_SINK" speaker-test -D pulse -c 1 -t sine -f 440
```

## Test the microphone separately

```bash
SAVI_SOURCE=$(pactl list short sources | awk '/alsa_input.*Poly_Savi/ {print $2; exit}')
parecord --device="$SAVI_SOURCE" --file-format=wav --rate=16000 --channels=1 /tmp/savi-mic-test.wav
```

Speak, stop recording with Ctrl+C, then play the recording through a known working output using `paplay /tmp/savi-mic-test.wav` (select that output in Sound Settings first).

Microphone recording quality was not independently verified during the original incident.

If the headset still announces that the base is disconnected after a power reset, investigate DECT subscription using the model-specific Poly instructions before altering Linux audio settings.
