"""Command execution for Linux agent."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def execute_command(
    command_type: str, payload: dict | None = None
) -> tuple[bool, str | None, dict | None]:
    """
    Execute a command from the server.

    Returns (success, error_message, result_data).
    """
    try:
        handler = COMMAND_HANDLERS.get(command_type)
        if not handler:
            return False, f"Unknown command type: {command_type}", None

        return handler(payload or {})
    except Exception as e:
        logger.exception(f"Command {command_type} failed")
        return False, str(e), None


def cmd_lock(payload: dict) -> tuple[bool, str | None, dict | None]:
    """Lock the screen (requires display)."""
    try:
        # Try various lock commands
        for cmd in [
            ["loginctl", "lock-sessions"],
            ["xdg-screensaver", "lock"],
            ["gnome-screensaver-command", "-l"],
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0:
                    return True, None, {"method": cmd[0]}
            except FileNotFoundError:
                continue

        return False, "No screen lock command available", None
    except Exception as e:
        return False, str(e), None


def cmd_ring(payload: dict) -> tuple[bool, str | None, dict | None]:
    """Play a sound to help locate the device."""
    try:
        # Try various sound commands
        for cmd in [
            ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
            ["aplay", "/usr/share/sounds/alsa/Front_Center.wav"],
            ["spd-say", "Device Valet is looking for this device"],
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                if result.returncode == 0:
                    return True, None, {"method": cmd[0]}
            except FileNotFoundError:
                continue

        return False, "No sound command available", None
    except Exception as e:
        return False, str(e), None


def cmd_message(payload: dict) -> tuple[bool, str | None, dict | None]:
    """Display a message to the user."""
    message = payload.get("message", "Message from DeviceValet")
    title = payload.get("title", "DeviceValet")

    try:
        # Try various notification commands
        for cmd in [
            ["notify-send", "-u", "critical", title, message],
            ["zenity", "--info", "--title", title, "--text", message],
            ["kdialog", "--msgbox", message, "--title", title],
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=10)
                if result.returncode == 0:
                    return True, None, {"method": cmd[0]}
            except FileNotFoundError:
                continue

        return False, "No notification command available", None
    except Exception as e:
        return False, str(e), None


def cmd_reboot(payload: dict) -> tuple[bool, str | None, dict | None]:
    """Reboot the system."""
    delay = payload.get("delay_seconds", 60)

    try:
        result = subprocess.run(
            ["shutdown", "-r", f"+{delay // 60}", "DeviceValet requested reboot"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, None, {"scheduled_in_seconds": delay}
        return False, result.stderr.decode(), None
    except Exception as e:
        return False, str(e), None


def cmd_shutdown(payload: dict) -> tuple[bool, str | None, dict | None]:
    """Shutdown the system."""
    delay = payload.get("delay_seconds", 60)

    try:
        result = subprocess.run(
            ["shutdown", "-h", f"+{delay // 60}", "DeviceValet requested shutdown"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, None, {"scheduled_in_seconds": delay}
        return False, result.stderr.decode(), None
    except Exception as e:
        return False, str(e), None


def cmd_run_script(payload: dict) -> tuple[bool, str | None, dict | None]:
    """Run a script (with safety restrictions)."""
    script = payload.get("script", "")
    timeout = min(payload.get("timeout", 60), 300)  # Max 5 minutes

    if not script:
        return False, "No script provided", None

    # Safety check - only allow certain commands
    allowed_prefixes = [
        "apt update",
        "apt upgrade",
        "systemctl restart",
        "systemctl status",
    ]

    if not any(script.strip().startswith(prefix) for prefix in allowed_prefixes):
        return False, "Script not in allowed list", None

    try:
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            timeout=timeout,
        )
        return (
            result.returncode == 0,
            result.stderr.decode() if result.returncode != 0 else None,
            {
                "stdout": result.stdout.decode()[:1000],  # Limit output size
                "return_code": result.returncode,
            },
        )
    except subprocess.TimeoutExpired:
        return False, "Script timed out", None
    except Exception as e:
        return False, str(e), None


def cmd_install_package(payload: dict) -> tuple[bool, str | None, dict | None]:
    """Install a package."""
    package = payload.get("package", "")

    if not package:
        return False, "No package specified", None

    # Safety: only allow alphanumeric package names
    if not package.replace("-", "").replace("_", "").isalnum():
        return False, "Invalid package name", None

    try:
        # Detect package manager and install
        for pm_cmd in [
            ["apt", "install", "-y", package],
            ["pacman", "-S", "--noconfirm", package],
            ["dnf", "install", "-y", package],
        ]:
            try:
                result = subprocess.run(pm_cmd, capture_output=True, timeout=300)
                if result.returncode == 0:
                    return True, None, {"package": package, "manager": pm_cmd[0]}
            except FileNotFoundError:
                continue

        return False, "No supported package manager found", None
    except subprocess.TimeoutExpired:
        return False, "Package installation timed out", None
    except Exception as e:
        return False, str(e), None


# Command handler registry
COMMAND_HANDLERS = {
    "lock": cmd_lock,
    "ring": cmd_ring,
    "message": cmd_message,
    "reboot": cmd_reboot,
    "shutdown": cmd_shutdown,
    "run_script": cmd_run_script,
    "install_package": cmd_install_package,
}
