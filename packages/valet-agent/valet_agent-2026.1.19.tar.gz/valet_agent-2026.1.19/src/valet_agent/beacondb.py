"""BeaconDB API client for WiFi-based geolocation.

BeaconDB is a privacy-focused, self-hostable WiFi/cell geolocation service
compatible with the Ichnaea (Mozilla Location Service) API format.

Features:
- Geolocate: Look up location from WiFi observations
- Geosubmit: Contribute observations when GPS is available

See: https://github.com/beacondb/beacondb
"""

import logging
from dataclasses import dataclass
from enum import Enum

import httpx

from valet_agent.wifi import WifiObservation

logger = logging.getLogger(__name__)

# Default to public BeaconDB instance
DEFAULT_BASE_URL = "https://api.beacondb.net"
DEFAULT_TIMEOUT = 5.0

# Minimum networks required for reasonable accuracy
MIN_WIFI_NETWORKS = 2


class LocationSource(str, Enum):
    """Location source type."""

    GPS = "gps"
    WIFI = "wifi"
    CELL = "cell"
    IP = "ip"


@dataclass
class GeolocateResult:
    """Result from BeaconDB geolocate API."""

    latitude: float
    longitude: float
    accuracy: float  # Accuracy in meters
    source: LocationSource


@dataclass
class GeosubmitPosition:
    """Position data for geosubmit."""

    latitude: float
    longitude: float
    accuracy: float


class BeaconDbClient:
    """BeaconDB API client for WiFi-based geolocation."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    def geolocate(
        self,
        wifi_networks: list[WifiObservation],
        consider_ip: bool = True,
    ) -> GeolocateResult | None:
        """
        Geolocate using WiFi observations.

        Args:
            wifi_networks: List of WiFi observations from wifi.scan_wifi()
            consider_ip: Whether to use IP fallback if WiFi lookup fails

        Returns:
            GeolocateResult with location, or None on failure
        """
        if len(wifi_networks) < MIN_WIFI_NETWORKS:
            logger.debug(
                f"Not enough WiFi networks for geolocation "
                f"({len(wifi_networks)} < {MIN_WIFI_NETWORKS})"
            )
            return None

        try:
            request_data = {
                "wifiAccessPoints": [
                    {
                        "macAddress": wifi.mac_address,
                        "signalStrength": wifi.signal_strength,
                        **({"channel": wifi.channel} if wifi.channel > 0 else {}),
                        **({"frequency": wifi.frequency} if wifi.frequency > 0 else {}),
                    }
                    for wifi in wifi_networks
                ],
                "considerIp": consider_ip,
            }

            response = self.client.post("/v1/geolocate", json=request_data)

            if response.status_code != 200:
                logger.warning(f"Geolocate failed: {response.status_code} {response.text}")
                return None

            data = response.json()
            location = data.get("location", {})
            fallback = data.get("fallback")

            result = GeolocateResult(
                latitude=location.get("lat", 0),
                longitude=location.get("lng", 0),
                accuracy=data.get("accuracy", 0),
                source=LocationSource.IP if fallback == "ipf" else LocationSource.WIFI,
            )

            logger.debug(
                f"Geolocate success: {result.latitude}, {result.longitude} "
                f"(accuracy: {result.accuracy}m, source: {result.source.value})"
            )

            return result

        except httpx.TimeoutException:
            logger.warning("Geolocate request timed out")
            return None
        except Exception as e:
            logger.error(f"Geolocate error: {e}")
            return None

    def geosubmit(
        self,
        position: GeosubmitPosition,
        wifi_networks: list[WifiObservation],
    ) -> bool:
        """
        Submit WiFi observations with known position to BeaconDB.

        This contributes to the crowdsourced location database.
        Should only be called when position accuracy is good (< 50m).

        Args:
            position: Known position (e.g., from GPS or another source)
            wifi_networks: WiFi observations at this position

        Returns:
            True if submission succeeded
        """
        if not wifi_networks:
            logger.debug("No WiFi networks to submit")
            return False

        # Only submit if accuracy is good
        if position.accuracy > 50:
            logger.debug(f"Skipping geosubmit: accuracy too low ({position.accuracy}m > 50m)")
            return False

        try:
            import time

            request_data = {
                "items": [
                    {
                        "timestamp": int(time.time() * 1000),
                        "position": {
                            "latitude": position.latitude,
                            "longitude": position.longitude,
                            "accuracy": position.accuracy,
                        },
                        "wifiAccessPoints": [
                            {
                                "macAddress": wifi.mac_address,
                                "signalStrength": wifi.signal_strength,
                                **({"channel": wifi.channel} if wifi.channel > 0 else {}),
                                **({"frequency": wifi.frequency} if wifi.frequency > 0 else {}),
                            }
                            for wifi in wifi_networks
                        ],
                    }
                ]
            }

            response = self.client.post("/v2/geosubmit", json=request_data)

            if response.status_code in (200, 204):
                logger.debug(
                    f"Geosubmit success: contributed {len(wifi_networks)} WiFi observations"
                )
                return True
            else:
                logger.warning(f"Geosubmit failed: {response.status_code} {response.text}")
                return False

        except httpx.TimeoutException:
            logger.warning("Geosubmit request timed out")
            return False
        except Exception as e:
            logger.error(f"Geosubmit error: {e}")
            return False

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None


def get_location_from_wifi(
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = DEFAULT_TIMEOUT,
) -> GeolocateResult | None:
    """
    Convenience function to get location from WiFi.

    Scans WiFi networks and queries BeaconDB for position.

    Args:
        base_url: BeaconDB API URL
        timeout: Request timeout in seconds

    Returns:
        GeolocateResult with location, or None on failure
    """
    from valet_agent.wifi import scan_wifi

    wifi_networks = scan_wifi()
    if not wifi_networks:
        logger.debug("No WiFi networks found")
        return None

    client = BeaconDbClient(base_url=base_url, timeout=timeout)
    try:
        return client.geolocate(wifi_networks)
    finally:
        client.close()
