"""API client for communicating with DeviceValet server."""

import logging
from typing import Any

import httpx

from valet_agent import __version__
from valet_agent.collector import SystemInfo
from valet_agent.config import AgentConfig

logger = logging.getLogger(__name__)


class ValetClient:
    """HTTP client for DeviceValet API."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.base_url = config.server_url.rstrip("/")
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.auth_token}",
                    "User-Agent": f"valet-agent/{__version__}",
                },
                timeout=30.0,
            )
        return self._client

    def checkin(self, system_info: SystemInfo) -> dict[str, Any]:
        """
        Send check-in to server.

        Returns server response with commands and policy updates.
        """
        payload = {
            "agent_version": __version__,
            "manufacturer": system_info.manufacturer,
            "model": system_info.model,
            "serial_number": system_info.serial_number,
            "os_version": system_info.os_version,
            "storage_total_gb": system_info.storage_total_gb,
            "storage_free_gb": system_info.storage_free_gb,
            "memory_total_mb": system_info.memory_total_mb,
            "memory_free_mb": system_info.memory_free_mb,
            "uptime_seconds": system_info.uptime_seconds,
            "ip_address": system_info.ip_address,
            "mac_address": system_info.mac_address,
            "connection_type": system_info.connection_type,
            "platform_data": system_info.platform_data,
            # Location (WiFi-based via BeaconDB)
            "latitude": system_info.latitude,
            "longitude": system_info.longitude,
            "location_source": system_info.location_source,
            "location_accuracy": system_info.location_accuracy,
        }

        response = self.client.post("/api/v1/agent/checkin", json=payload)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def report_command_result(
        self,
        command_id: str,
        success: bool,
        error_message: str | None = None,
        result_data: dict | None = None,
    ) -> None:
        """Report result of command execution."""
        from datetime import datetime, timezone

        payload = {
            "command_id": command_id,
            "success": success,
            "error_message": error_message,
            "result_data": result_data,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        response = self.client.post("/api/v1/agent/command-result", json=payload)
        response.raise_for_status()

    def report_event(
        self,
        event_type: str,
        message: str,
        severity: str = "info",
        data: dict | None = None,
    ) -> None:
        """Report an event to the server."""
        params: dict[str, Any] = {
            "event_type": event_type,
            "message": message,
            "severity": severity,
        }
        if data:
            params["data"] = data

        response = self.client.post("/api/v1/agent/event", params=params)
        response.raise_for_status()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
