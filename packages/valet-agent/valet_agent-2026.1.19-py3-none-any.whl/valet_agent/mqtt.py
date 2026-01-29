"""MQTT client for real-time device communication.

Topic Structure (matches backend and Android agent):
    devicevalet/org/{org_id}/devices/{device_id}/commands    - Commands TO device
    devicevalet/org/{org_id}/devices/{device_id}/telemetry   - Telemetry FROM device
    devicevalet/org/{org_id}/devices/{device_id}/status      - Status (online/offline)
    devicevalet/org/{org_id}/devices/{device_id}/ack         - Command acknowledgments
"""

import json
import logging
import ssl
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

# Topic prefix
TOPIC_PREFIX = "devicevalet"


@dataclass
class MqttConfig:
    """MQTT connection configuration."""

    broker_url: str  # ws://host:port/mqtt or wss://host:port/mqtt
    org_id: str
    device_id: str
    username: str | None = None
    password: str | None = None
    keepalive: int = 60
    reconnect_delay_min: float = 1.0
    reconnect_delay_max: float = 120.0


class MqttTopics:
    """MQTT topic helpers."""

    @staticmethod
    def commands(org_id: str, device_id: str) -> str:
        """Topic for receiving commands FROM backend."""
        return f"{TOPIC_PREFIX}/org/{org_id}/devices/{device_id}/commands"

    @staticmethod
    def telemetry(org_id: str, device_id: str) -> str:
        """Topic for publishing telemetry TO backend."""
        return f"{TOPIC_PREFIX}/org/{org_id}/devices/{device_id}/telemetry"

    @staticmethod
    def status(org_id: str, device_id: str) -> str:
        """Topic for device status (LWT)."""
        return f"{TOPIC_PREFIX}/org/{org_id}/devices/{device_id}/status"

    @staticmethod
    def ack(org_id: str, device_id: str) -> str:
        """Topic for command acknowledgments."""
        return f"{TOPIC_PREFIX}/org/{org_id}/devices/{device_id}/ack"

    @staticmethod
    def broadcast(org_id: str) -> str:
        """Topic for org-wide broadcast commands."""
        return f"{TOPIC_PREFIX}/org/{org_id}/broadcast"


class MqttClient:
    """
    MQTT client for DeviceValet Linux agent.

    Features:
    - WebSocket connection (through Caddy reverse proxy)
    - Automatic reconnection with exponential backoff
    - Last Will and Testament for offline detection
    - Thread-safe publish
    """

    def __init__(self, config: MqttConfig) -> None:
        self.config = config
        self._client: mqtt.Client | None = None
        self._connected = False
        self._shutdown = False
        self._reconnect_delay = config.reconnect_delay_min
        self._lock = threading.Lock()

        # Callbacks
        self.on_command: Callable[[str, dict], None] | None = None
        self.on_connect: Callable[[bool], None] | None = None

    def connect(self) -> bool:
        """
        Connect to the MQTT broker.

        Returns:
            True if connection initiated successfully
        """
        if self._connected:
            logger.warning("Already connected")
            return True

        try:
            # Parse broker URL
            parsed = urlparse(self.config.broker_url)
            use_tls = parsed.scheme in ("wss", "mqtts")
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if use_tls else 9001)
            path = parsed.path or "/mqtt"

            # Create client with WebSocket transport
            client_id = f"linux-{self.config.device_id[:12]}"
            self._client = mqtt.Client(
                client_id=client_id,
                transport="websockets",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            )

            # Set WebSocket path
            self._client.ws_set_options(path=path)

            # Set callbacks
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message

            # Authentication
            if self.config.username and self.config.password:
                self._client.username_pw_set(
                    self.config.username,
                    self.config.password,
                )

            # TLS for secure connections
            if use_tls:
                self._client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

            # Last Will and Testament - published if we disconnect unexpectedly
            lwt_topic = MqttTopics.status(self.config.org_id, self.config.device_id)
            self._client.will_set(lwt_topic, "offline", qos=1, retain=True)

            # Connect
            logger.info(f"Connecting to MQTT broker: {host}:{port}{path}")
            self._client.connect_async(host, port, self.config.keepalive)
            self._client.loop_start()

            return True

        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self._shutdown = True

        if self._client and self._connected:
            try:
                # Publish offline status before disconnecting
                status_topic = MqttTopics.status(
                    self.config.org_id,
                    self.config.device_id,
                )
                self._client.publish(status_topic, "offline", qos=1, retain=True)
                self._client.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._client.loop_stop()

        self._connected = False
        logger.info("MQTT disconnected")

    def publish_telemetry(self, data: dict[str, Any]) -> bool:
        """
        Publish telemetry data.

        Args:
            data: Telemetry payload

        Returns:
            True if published successfully
        """
        topic = MqttTopics.telemetry(self.config.org_id, self.config.device_id)
        return self._publish(topic, data, qos=0)

    def publish_ack(self, command_id: str, success: bool, error: str | None = None) -> bool:
        """
        Publish command acknowledgment.

        Args:
            command_id: ID of the command being acknowledged
            success: Whether command executed successfully
            error: Error message if failed

        Returns:
            True if published successfully
        """
        topic = MqttTopics.ack(self.config.org_id, self.config.device_id)
        payload = {
            "command_id": command_id,
            "success": success,
            "error": error,
            "timestamp": time.time(),
        }
        return self._publish(topic, payload, qos=1)

    def _publish(self, topic: str, payload: dict, qos: int = 0, retain: bool = False) -> bool:
        """Internal publish method."""
        if not self._client or not self._connected:
            logger.warning("Cannot publish: not connected")
            return False

        with self._lock:
            try:
                result = self._client.publish(
                    topic,
                    json.dumps(payload),
                    qos=qos,
                    retain=retain,
                )
                return result.rc == mqtt.MQTT_ERR_SUCCESS
            except Exception as e:
                logger.error(f"Publish failed: {e}")
                return False

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict,
        reason_code: mqtt.ReasonCode,
        properties: Any = None,
    ) -> None:
        """Handle connection established."""
        if reason_code == mqtt.CONNACK_ACCEPTED or reason_code == 0:
            self._connected = True
            self._reconnect_delay = self.config.reconnect_delay_min
            logger.info("MQTT connected")

            # Subscribe to commands
            commands_topic = MqttTopics.commands(
                self.config.org_id,
                self.config.device_id,
            )
            broadcast_topic = MqttTopics.broadcast(self.config.org_id)

            client.subscribe([(commands_topic, 1), (broadcast_topic, 1)])
            logger.debug(f"Subscribed to: {commands_topic}, {broadcast_topic}")

            # Publish online status
            status_topic = MqttTopics.status(
                self.config.org_id,
                self.config.device_id,
            )
            client.publish(status_topic, "online", qos=1, retain=True)

            # Notify callback
            if self.on_connect:
                self.on_connect(True)
        else:
            logger.error(f"MQTT connection failed: {reason_code}")
            if self.on_connect:
                self.on_connect(False)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: mqtt.DisconnectFlags | None = None,
        reason_code: mqtt.ReasonCode | None = None,
        properties: Any = None,
    ) -> None:
        """Handle disconnection."""
        self._connected = False

        if self._shutdown:
            logger.info("MQTT disconnected (shutdown)")
            return

        logger.warning(f"MQTT disconnected: {reason_code}")

        # Schedule reconnect with exponential backoff
        if not self._shutdown:
            logger.info(f"Reconnecting in {self._reconnect_delay:.1f}s...")
            time.sleep(self._reconnect_delay)
            self._reconnect_delay = min(
                self._reconnect_delay * 2,
                self.config.reconnect_delay_max,
            )
            try:
                client.reconnect()
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming message."""
        try:
            topic = message.topic
            payload = json.loads(message.payload.decode())

            logger.debug(f"MQTT message on {topic}: {payload}")

            # Extract command type from payload
            if self.on_command:
                command_type = payload.get("type")
                if command_type:
                    self.on_command(command_type, payload)

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in MQTT message: {e}")
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    @property
    def connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected
