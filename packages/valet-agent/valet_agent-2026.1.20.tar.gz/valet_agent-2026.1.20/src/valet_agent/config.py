"""Agent configuration."""

import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_config_dir() -> Path:
    """Get config directory based on user context."""
    if os.getuid() == 0:
        # Running as root → system config
        return Path("/etc/valet-agent")
    # Running as user → XDG config
    xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(xdg_config) / "valet-agent"


def _get_data_dir() -> Path:
    """Get data directory based on user context."""
    if os.getuid() == 0:
        # Running as root → system data
        return Path("/var/lib/valet-agent")
    # Running as user → XDG data
    xdg_data = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
    return Path(xdg_data) / "valet-agent"


def _get_log_file() -> Path:
    """Get log file path based on user context."""
    if os.getuid() == 0:
        # Running as root → system log
        return Path("/var/log/valet-agent.log")
    # Running as user → XDG state (or data fallback)
    xdg_state = os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
    return Path(xdg_state) / "valet-agent" / "agent.log"


def _get_env_file() -> Path:
    """Get env file path based on user context."""
    config_dir = _get_config_dir()
    return config_dir / "agent.env"


class AgentConfig(BaseSettings):
    """Agent configuration loaded from environment or config file.

    Configuration sources (in order of precedence):
    1. Environment variables (VALET_* prefix)
    2. Config file (agent.env in config directory)
    3. Default values

    Paths auto-detect based on user context:
    - Root user: /etc/valet-agent, /var/lib/valet-agent, /var/log/
    - Regular user: ~/.config/valet-agent, ~/.local/share/valet-agent, ~/.local/state/
    """

    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
        env_prefix="VALET_",
        case_sensitive=False,
    )

    # Server connection (REQUIRED - no default)
    server_url: str = ""
    auth_token: str = ""

    # Device identity (set during enrollment)
    device_id: str = ""
    organization_id: str = ""

    # Check-in settings
    checkin_interval_seconds: int = 300  # 5 minutes

    # Features
    report_location: bool = True  # Enable WiFi-based location via BeaconDB
    report_packages: bool = True
    report_services: bool = True

    # BeaconDB (WiFi Geolocation)
    beacondb_enabled: bool = True
    beacondb_url: str = "https://api.beacondb.net"  # Public service (or self-hosted)
    beacondb_contribute: bool = True  # Submit WiFi observations back
    beacondb_timeout: float = 5.0  # Request timeout in seconds

    # MQTT (real-time commands)
    mqtt_enabled: bool = True
    mqtt_broker_url: str = ""  # ws://host:port/mqtt or wss://host:port/mqtt
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_keepalive: int = 60

    # Paths (auto-detected based on user context, can be overridden)
    config_dir: Path = _get_config_dir()
    data_dir: Path = _get_data_dir()
    log_file: Path = _get_log_file()

    @field_validator("server_url")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Ensure server_url is configured and not a placeholder."""
        if not v:
            return v  # Allow empty for --help, validate at runtime
        if "example.com" in v or "example.org" in v:
            raise ValueError(
                "server_url contains placeholder domain. "
                "Set VALET_SERVER_URL or configure agent.env"
            )
        return v.rstrip("/")  # Normalize: remove trailing slash

    def ensure_directories(self) -> None:
        """Create config and data directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def is_enrolled(self) -> bool:
        """Check if device has been enrolled."""
        return bool(self.device_id and self.auth_token and self.server_url)

    def validate_for_operation(self) -> None:
        """Validate config is complete for agent operation.

        Raises:
            ValueError: If required settings are missing.
        """
        errors = []
        if not self.server_url:
            errors.append("server_url is required (set VALET_SERVER_URL)")
        if not self.auth_token:
            errors.append("auth_token is required (run 'valet-agent enroll' first)")
        if not self.device_id:
            errors.append("device_id is required (run 'valet-agent enroll' first)")
        if errors:
            raise ValueError("Configuration incomplete:\n  - " + "\n  - ".join(errors))


def load_config() -> AgentConfig:
    """Load agent configuration."""
    return AgentConfig()


def get_default_paths() -> dict[str, Path]:
    """Get default paths for current user context (useful for CLI help)."""
    return {
        "config_dir": _get_config_dir(),
        "data_dir": _get_data_dir(),
        "log_file": _get_log_file(),
        "env_file": _get_env_file(),
    }
