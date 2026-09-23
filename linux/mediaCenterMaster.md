# Media Center Master on Linux

## Purpose

Media Center Master (MCM) runs under Wine while qBittorrent runs as a native Linux application. MCM discovers media and launches magnet links; qBittorrent performs the download. The hand-off is guarded so qBittorrent cannot be launched by a magnet unless Private Internet Access (PIA) is connected and Internet traffic is routed through the VPN.

`organiseMyVideo` remains authoritative for moving completed downloads into the managed media library.

## Components

- MCM Wine prefix: `~/.wine-mcm`
- Native qBittorrent: `/usr/bin/qbittorrent`
- PIA VPN interface: `tun0`
- Physical network interface on the tested machine: `enp42s0`
- qBittorrent incomplete downloads: `/mnt/video2/Downloads`
- qBittorrent completed/handoff directory: `/mnt/video2/toFile`
- VPN guard: `~/bin/qbittorrent-vpn`
- Linux magnet handler: `~/.local/share/applications/qbittorrent-vpn.desktop`

## Workflow

```text
MCM (Wine)
    |
    | magnet:
    v
winebrowser.exe
    |
    v
Linux x-scheme-handler/magnet
    |
    v
~/bin/qbittorrent-vpn
    |
    +-- tun0 absent -----------------> BLOCK
    |
    +-- Internet not routed via tun0 -> BLOCK
    |
    v
native qBittorrent
    |
    | bound to tun0
    v
/mnt/video2/Downloads
    |
    | download complete
    v
/mnt/video2/toFile
    |
    v
organiseMyVideo
    |
    v
managed media library
```

## MCM startup sequence

MCM licensing and application update checks must be completed before enabling the VPN. MCM's torrent scraping then runs with the VPN connected.

1. Leave PIA disconnected.
2. Start MCM.
3. Allow MCM to complete licence validation.
4. Check for and install any MCM application updates.
5. Connect PIA.
6. Verify that Internet traffic is routed through `tun0`.
7. Run the required on-demand MCM torrent/new-release scrape.
8. MCM launches an accepted magnet link.
9. The guarded Linux magnet handler passes it to native qBittorrent only when the VPN checks succeed.
10. qBittorrent downloads to the media staging directories.
11. `organiseMyVideo` moves completed media from `/mnt/video2/toFile` into the final library.
12. MCM may subsequently scan and maintain the resulting library.

Verify the VPN route with:

```bash
ip route get 1.1.1.1
```

A valid connected state includes `dev tun0`.

## Wine magnet protocol

Linux already associates magnet links with qBittorrent. The MCM Wine prefix also requires a Windows `magnet:` protocol registration.

The working Wine registration is:

```text
HKEY_CLASSES_ROOT\magnet
    (Default)       URL:Magnet Protocol
    URL Protocol

HKEY_CLASSES_ROOT\magnet\shell\open\command
    (Default)       "C:\windows\system32\winebrowser.exe" "%1"
```

It can be created with:

```bash
WINEPREFIX="$HOME/.wine-mcm" wine reg add \
'HKEY_CLASSES_ROOT\magnet' \
/ve /d 'URL:Magnet Protocol' /f

WINEPREFIX="$HOME/.wine-mcm" wine reg add \
'HKEY_CLASSES_ROOT\magnet' \
/v 'URL Protocol' /d '' /f

WINEPREFIX="$HOME/.wine-mcm" wine reg add \
'HKEY_CLASSES_ROOT\magnet\shell\open\command' \
/ve /d '"C:\windows\system32\winebrowser.exe" "%1"' /f
```

Verify with:

```bash
WINEPREFIX="$HOME/.wine-mcm" \
wine reg query 'HKEY_CLASSES_ROOT\magnet' /s
```

## VPN guard

Create `~/bin/qbittorrent-vpn`:

```bash
#!/usr/bin/env bash

VPN_INTERFACE="tun0"
QBITTORRENT="/usr/bin/qbittorrent"

if ! ip link show "$VPN_INTERFACE" >/dev/null 2>&1; then
    echo "qBittorrent blocked - VPN interface $VPN_INTERFACE is not available." >&2
    exit 1
fi

ROUTE="$(ip route get 1.1.1.1 2>/dev/null)" || {
    echo "qBittorrent blocked - unable to determine Internet route." >&2
    exit 1
}

if [[ "$ROUTE" != *"dev $VPN_INTERFACE"* ]]; then
    echo "qBittorrent blocked - Internet traffic is not routed through $VPN_INTERFACE." >&2
    exit 1
fi

exec "$QBITTORRENT" "$@"
```

Make it executable:

```bash
chmod +x ~/bin/qbittorrent-vpn
```

The guard deliberately checks both that `tun0` exists and that a public Internet route actually uses `tun0`.

## Linux magnet handler

Create `~/.local/share/applications/qbittorrent-vpn.desktop`:

```ini
[Desktop Entry]
Name=qBittorrent (VPN Required)
Exec=/home/andy/bin/qbittorrent-vpn %U
Terminal=false
Type=Application
MimeType=x-scheme-handler/magnet;
NoDisplay=true
```

Register it:

```bash
xdg-mime default qbittorrent-vpn.desktop x-scheme-handler/magnet
```

Verify:

```bash
xdg-mime query default x-scheme-handler/magnet
```

Expected result:

```text
qbittorrent-vpn.desktop
```

## qBittorrent VPN binding

In qBittorrent use:

**Tools -> Options -> Advanced -> Network interface -> tun0**

Leave the optional IP-address binding at all addresses. The PIA address can change on reconnection, while the interface name remains the stable binding.

This is the second protection layer. The launcher prevents a magnet from starting qBittorrent without the VPN, while qBittorrent's own interface binding prevents it from falling back to the physical network if the VPN subsequently disappears.

## Proven tests

The following end-to-end behaviour has been tested successfully.

### VPN disconnected

With qBittorrent closed and PIA disconnected, launching a magnet through the MCM Wine prefix does not start qBittorrent.

### VPN connected

With PIA connected and:

```text
ip route get 1.1.1.1
... dev tun0 ...
```

launching a magnet through the MCM Wine prefix starts native qBittorrent.

This proves the path:

```text
Wine -> winebrowser.exe -> Linux magnet handler -> VPN guard -> native qBittorrent
```

## MCM torrent settings

In **Preferences & Settings -> Torrents**:

- Enable torrenting downloads.
- Enable **Allow magnet links to launch locally**.
- Keep MCM's torrent auto-start behaviour separate from the magnet hand-off.
- Save T.V. and other torrent files to `J:\Torrents`.
- MCM's seed-count filtering should be reduced so qBittorrent can determine actual swarm availability. Use zero if MCM accepts zero as no minimum; otherwise use one.

The live MCM setting for magnet launching is:

```xml
<key name="Torrents_AllowMagnetLinks">True</key>
```

It can be checked with:

```bash
FILE="$HOME/.wine-mcm/drive_c/users/andy/AppData/Roaming/Peter Souza IV/Media Center Master/Profiles/Default__[internal]/settings.xml"

grep -n 'Torrents_AllowMagnetLinks' "$FILE"
```

Seed settings are:

```xml
<key name="Torrents_MinimumEpisodeSeeds">...</key>
<key name="Torrents_MinimumMovieSeeds">...</key>
```

Verify them with:

```bash
grep -nE 'Torrents_Minimum(Movie|Episode)Seeds' "$FILE"
```

## Responsibility boundaries

MCM is responsible for media discovery, torrent/magnet selection, and subsequent library metadata/maintenance.

qBittorrent is responsible for torrent downloading and swarm handling.

`organiseMyVideo` is authoritative for the initial move from `/mnt/video2/toFile` into the final managed media library. MCM must not compete with `organiseMyVideo` for that move.

## Future bootstrap work

The proven setup should ultimately be represented in `linuxBootstrap`, including:

- the dedicated MCM Wine prefix;
- MCM's Wine magnet protocol registration;
- the `~/bin/qbittorrent-vpn` guard;
- the guarded Linux magnet desktop handler;
- qBittorrent media paths;
- documentation of the required MCM -> licence/update -> VPN -> scrape startup sequence.

Automation must preserve the fail-closed VPN behaviour demonstrated above.
