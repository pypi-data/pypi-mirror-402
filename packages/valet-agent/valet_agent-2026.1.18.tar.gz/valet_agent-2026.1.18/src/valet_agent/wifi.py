"""WiFi network scanner for Linux devices.

Scans nearby WiFi access points for BeaconDB geolocation.
Supports NetworkManager (nmcli) and iwlist as fallback.

Privacy filtering:
- SSIDs containing "_nomap" are excluded (Google/Apple standard)
- SSIDs containing "_optout" are excluded
- Hidden networks (empty SSID) are excluded
"""

import logging
import re
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Privacy filter patterns (case-insensitive)
OPT_OUT_PATTERNS = ["_nomap", "_optout"]


@dataclass
class WifiObservation:
    """A WiFi network observation for geolocation."""

    mac_address: str  # MAC address in uppercase colon-separated format
    signal_strength: int  # Signal strength in dBm (typically -30 to -100)
    channel: int = 0  # WiFi channel number
    frequency: int = 0  # Frequency in MHz
    ssid: str | None = None  # SSID (for debugging, not sent to BeaconDB)


def scan_wifi() -> list[WifiObservation]:
    """
    Scan for nearby WiFi access points.

    Tries nmcli first (no root required), falls back to iwlist (may require root).

    Returns:
        List of WiFi observations filtered for privacy.
    """
    try:
        return scan_wifi_nmcli()
    except Exception as e:
        logger.debug(f"nmcli scan failed: {e}, trying iwlist")
        try:
            return scan_wifi_iwlist()
        except Exception as e2:
            logger.warning(f"WiFi scanning failed: {e2}")
            return []


def scan_wifi_nmcli() -> list[WifiObservation]:
    """
    Scan WiFi using NetworkManager CLI (nmcli).

    Requires NetworkManager to be running. Does not require root.

    Returns:
        List of WiFi observations.

    Raises:
        FileNotFoundError: If nmcli is not installed.
        subprocess.CalledProcessError: If scan fails.
    """
    # Trigger a scan first (may fail if already scanning, that's ok)
    try:
        subprocess.run(
            ["nmcli", "device", "wifi", "rescan"],
            capture_output=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        pass  # Scan might be in progress

    # Get scan results
    # Format: BSSID,SIGNAL,FREQ,SSID
    result = subprocess.run(
        [
            "nmcli",
            "-t",  # Terse output
            "-f",
            "BSSID,SIGNAL,FREQ,SSID",
            "device",
            "wifi",
            "list",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )

    observations = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        # nmcli uses escaped colons in MAC addresses, we need to handle this
        # Format: AA\:BB\:CC\:DD\:EE\:FF:signal:freq:SSID
        parts = line.split(":")

        if len(parts) < 4:
            continue

        # Reconstruct MAC address (first 6 parts with escaped colons)
        # MAC addresses look like: AA\:BB\:CC\:DD\:EE\:FF
        mac_parts: list[str] = []
        i = 0
        while i < len(parts) and len(mac_parts) < 6:
            part = parts[i]
            if part.endswith("\\"):
                # This part ends with \, next part is continuation
                mac_parts.append(part[:-1])
            else:
                mac_parts.append(part)
            i += 1

        if len(mac_parts) != 6:
            continue

        mac_address = ":".join(mac_parts).upper()

        # Remaining parts: signal, freq, ssid
        remaining = parts[i:]
        if len(remaining) < 2:
            continue

        try:
            signal = int(remaining[0])
            freq = int(remaining[1])
            ssid = ":".join(remaining[2:]) if len(remaining) > 2 else ""
        except ValueError:
            continue

        # Privacy filtering
        if not is_valid_for_geolocation(ssid, mac_address):
            continue

        # Convert signal percentage to dBm (nmcli reports percentage)
        # Rough conversion: -100 dBm = 0%, -50 dBm = 100%
        signal_dbm = -100 + signal // 2

        observations.append(
            WifiObservation(
                mac_address=mac_address,
                signal_strength=signal_dbm,
                channel=frequency_to_channel(freq),
                frequency=freq,
                ssid=ssid if ssid else None,
            )
        )

    logger.debug(f"nmcli scan found {len(observations)} valid networks")
    return observations


def scan_wifi_iwlist() -> list[WifiObservation]:
    """
    Scan WiFi using iwlist (wireless-tools).

    May require root privileges on some systems.

    Returns:
        List of WiFi observations.

    Raises:
        FileNotFoundError: If iwlist is not installed.
        subprocess.CalledProcessError: If scan fails.
    """
    # Find wireless interface
    interface = find_wireless_interface()
    if not interface:
        raise RuntimeError("No wireless interface found")

    # Run iwlist scan (may require sudo)
    result = subprocess.run(
        ["iwlist", interface, "scan"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        # Try with sudo if permission denied
        if (
            "permission denied" in result.stderr.lower()
            or "operation not permitted" in result.stderr.lower()
        ):
            result = subprocess.run(
                ["sudo", "-n", "iwlist", interface, "scan"],
                capture_output=True,
                text=True,
                timeout=30,
            )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, "iwlist", result.stderr)

    observations = []
    current_ap: dict = {}

    for line in result.stdout.split("\n"):
        line = line.strip()

        # New cell/AP
        if line.startswith("Cell"):
            if current_ap and current_ap.get("mac"):
                obs = build_observation(current_ap)
                if obs:
                    observations.append(obs)
            current_ap = {}

            # Extract MAC address
            match = re.search(r"Address: ([\dA-Fa-f:]+)", line)
            if match:
                current_ap["mac"] = match.group(1).upper()

        elif "ESSID:" in line:
            match = re.search(r'ESSID:"([^"]*)"', line)
            if match:
                current_ap["ssid"] = match.group(1)

        elif "Frequency:" in line:
            match = re.search(r"Frequency:([\d.]+)\s*GHz", line)
            if match:
                freq_ghz = float(match.group(1))
                current_ap["frequency"] = int(freq_ghz * 1000)

            match = re.search(r"Channel:(\d+)", line)
            if match:
                current_ap["channel"] = int(match.group(1))

        elif "Signal level" in line:
            # Format varies: "Signal level=-65 dBm" or "Signal level:65/100"
            match = re.search(r"Signal level[=:](-?\d+)", line)
            if match:
                signal = int(match.group(1))
                # If positive, it's a percentage
                if signal > 0:
                    signal = -100 + signal // 2
                current_ap["signal"] = signal

    # Don't forget the last AP
    if current_ap and current_ap.get("mac"):
        obs = build_observation(current_ap)
        if obs:
            observations.append(obs)

    logger.debug(f"iwlist scan found {len(observations)} valid networks")
    return observations


def build_observation(ap: dict) -> WifiObservation | None:
    """Build a WifiObservation from parsed AP data."""
    mac = ap.get("mac")
    ssid = ap.get("ssid", "")

    if not mac or not is_valid_for_geolocation(ssid, mac):
        return None

    return WifiObservation(
        mac_address=mac,
        signal_strength=ap.get("signal", -80),
        channel=ap.get("channel", 0),
        frequency=ap.get("frequency", 0),
        ssid=ssid if ssid else None,
    )


def find_wireless_interface() -> str | None:
    """Find the first wireless interface."""
    try:
        # Check /sys/class/net/*/wireless
        import os

        for iface in os.listdir("/sys/class/net"):
            wireless_path = f"/sys/class/net/{iface}/wireless"
            if os.path.isdir(wireless_path):
                return iface
    except OSError:
        pass

    # Fallback: try common names
    import shutil

    for name in ["wlan0", "wlp2s0", "wlp3s0", "wifi0"]:
        if shutil.which("ip"):
            result = subprocess.run(
                ["ip", "link", "show", name],
                capture_output=True,
            )
            if result.returncode == 0:
                return name

    return None


def is_valid_for_geolocation(ssid: str, mac_address: str) -> bool:
    """
    Check if a network is valid for geolocation.
    Filters out opted-out networks and invalid entries.
    """
    # Skip networks that opted out of location services
    if ssid:
        ssid_lower = ssid.lower()
        for pattern in OPT_OUT_PATTERNS:
            if pattern in ssid_lower:
                logger.debug(f"Filtered opt-out network: {ssid}")
                return False

    # Skip networks with invalid MAC addresses
    if not mac_address or mac_address == "00:00:00:00:00:00":
        return False

    # Skip locally administered addresses (randomized MACs)
    # Bit 1 of first octet indicates locally administered
    try:
        first_octet = int(mac_address.split(":")[0], 16)
        if first_octet & 0x02:
            logger.debug(f"Filtered locally administered MAC: {mac_address}")
            return False
    except (ValueError, IndexError):
        return False

    return True


def frequency_to_channel(freq: int) -> int:
    """Convert WiFi frequency to channel number."""
    if 2412 <= freq <= 2484:
        return (freq - 2412) // 5 + 1  # 2.4 GHz
    elif 5170 <= freq <= 5825:
        return (freq - 5170) // 5 + 34  # 5 GHz
    elif 5925 <= freq <= 7125:
        return (freq - 5925) // 5 + 1  # 6 GHz (WiFi 6E)
    return 0
