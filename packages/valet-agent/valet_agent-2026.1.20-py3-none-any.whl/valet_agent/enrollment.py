"""Device enrollment for DeviceValet Linux Agent."""

import hashlib
import platform
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from valet_agent.collector import get_dmi_info, get_primary_ip, get_serial_number


def _generate_hardware_id() -> str:
    """
    Generate a unique hardware identifier for this Linux device.

    Similar to Android's hardware_id which combines IMEI + Serial + Build.FINGERPRINT,
    for Linux we combine: machine-id + serial_number + hostname + DMI info.
    """
    components = []

    # /etc/machine-id is unique per installation
    machine_id_path = Path("/etc/machine-id")
    if machine_id_path.exists():
        components.append(machine_id_path.read_text().strip())

    # DMI serial number (if available)
    serial = get_serial_number()
    if serial:
        components.append(serial)

    # Hostname
    components.append(socket.gethostname())

    # DMI product info
    vendor = get_dmi_info("sys_vendor")
    product = get_dmi_info("product_name")
    if vendor:
        components.append(vendor)
    if product:
        components.append(product)

    # Combine and hash
    combined = "|".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()


def collect_enrollment_info(token: str) -> dict[str, Any]:
    """
    Collect system information for enrollment.

    Returns a dict matching the backend DeviceEnrollRequest schema.
    """
    ip_address, mac_address = get_primary_ip()

    return {
        "enrollment_token": token,
        "hardware_id": _generate_hardware_id(),
        "serial_number": get_serial_number(),
        "manufacturer": get_dmi_info("sys_vendor") or "Unknown",
        "model": get_dmi_info("product_name") or "Linux Device",
        "os_version": f"{platform.system()} {platform.release()}",
        "agent_version": _get_agent_version(),
        # Note: latitude/longitude not included - Linux uses WiFi geolocation after enrollment
    }


def _get_agent_version() -> str:
    """Get the agent version."""
    try:
        from importlib.metadata import version

        return version("valet-agent")
    except Exception:
        return "2026.1.19"


def derive_mqtt_url(server_url: str) -> str:
    """Derive MQTT WebSocket URL from server URL."""
    parsed = urlparse(server_url)

    # Convert https to wss, http to ws
    if parsed.scheme == "https":
        ws_scheme = "wss"
    else:
        ws_scheme = "ws"

    # Use same host, add /mqtt path
    return f"{ws_scheme}://{parsed.netloc}/mqtt"


def enroll_device(
    server_url: str,
    token: str,
    config_dir: Path,
    mqtt_url: str | None = None,
) -> dict[str, Any]:
    """
    Enroll this device with the DeviceValet server.

    Args:
        server_url: Base URL of the DeviceValet API
        token: Enrollment token from dashboard
        config_dir: Directory to save configuration
        mqtt_url: Optional MQTT broker URL (derived from server_url if not set)

    Returns:
        Dict with 'success', 'device_id', 'device_name', 'organization_name', or 'error'
    """
    # Normalize server URL
    server_url = server_url.rstrip("/")
    if not server_url.endswith("/api/v1"):
        server_url = f"{server_url}/api/v1"

    # Collect device info (includes hardware_id and enrollment_token)
    device_info = collect_enrollment_info(token)

    # Make enrollment request
    # Endpoint: POST /api/v1/enrollments/public/{token}/enroll
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{server_url}/enrollments/public/{token}/enroll",
                json=device_info,
                headers={
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 401:
                return {"success": False, "error": "Invalid or expired enrollment token"}

            if response.status_code == 404:
                return {"success": False, "error": "Invalid enrollment token"}

            if response.status_code == 409:
                return {
                    "success": False,
                    "error": "Device already enrolled (duplicate serial number)",
                }

            if response.status_code == 410:
                # Token expired or max uses reached
                error_detail = response.json().get("detail", "Enrollment token is no longer valid")
                return {"success": False, "error": error_detail}

            response.raise_for_status()
            data = response.json()

    except httpx.ConnectError:
        return {"success": False, "error": f"Cannot connect to {server_url}"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Connection timed out"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"Server error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Extract credentials from response (DeviceEnrollResponse schema)
    device_id = data.get("device_id")
    auth_token = data.get("device_token")  # JWT for device auth
    organization_id = data.get("organization_id")
    device_name = data.get("device_name", "Unknown")
    organization_name = data.get("organization_name", "Unknown")

    if not device_id or not auth_token:
        return {"success": False, "error": "Invalid response from server (missing credentials)"}

    # Use MQTT URL from server response, CLI arg, or derive from server URL
    if not mqtt_url:
        # Server response includes mqtt_url
        mqtt_url = data.get("mqtt_url")
    if not mqtt_url:
        # Fallback: derive from server URL
        base_url = server_url.rsplit("/api/v1", 1)[0]
        mqtt_url = derive_mqtt_url(base_url)

    # Create config directory
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)

    # Write configuration file
    config_file = config_dir / "agent.env"
    base_url = server_url.rsplit("/api/v1", 1)[0]

    config_content = f"""# DeviceValet Linux Agent Configuration
# Generated during enrollment - do not edit manually

# Server connection
VALET_SERVER_URL={base_url}
VALET_AUTH_TOKEN={auth_token}

# Device identity (from enrollment)
VALET_DEVICE_ID={device_id}
VALET_ORGANIZATION_ID={organization_id}

# Check-in settings
VALET_CHECKIN_INTERVAL_SECONDS=300

# Features
VALET_REPORT_LOCATION=true
VALET_REPORT_PACKAGES=true
VALET_REPORT_SERVICES=true

# WiFi Geolocation (BeaconDB)
VALET_BEACONDB_ENABLED=true
VALET_BEACONDB_URL=https://api.beacondb.net
VALET_BEACONDB_CONTRIBUTE=true

# MQTT (real-time commands)
VALET_MQTT_ENABLED=true
VALET_MQTT_BROKER_URL={mqtt_url}
"""

    config_file.write_text(config_content)

    # Set restrictive permissions (readable only by root)
    config_file.chmod(0o600)

    return {
        "success": True,
        "device_id": device_id,
        "device_name": device_name,
        "organization_id": organization_id,
        "organization_name": organization_name,
        "config_file": str(config_file),
    }
