"""DeviceValet Linux Agent - Main daemon entry point."""

import logging
import signal
import sys
import time
from types import FrameType

from valet_agent.client import ValetClient
from valet_agent.collector import collect_system_info
from valet_agent.commands import execute_command
from valet_agent.config import AgentConfig, load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("valet-agent")

# Global flag for graceful shutdown
running = True

# Global MQTT client (optional)
mqtt_client = None


def signal_handler(signum: int, frame: FrameType | None) -> None:
    """Handle shutdown signals."""
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False


def handle_mqtt_command(command_type: str, payload: dict) -> None:
    """Handle command received via MQTT."""
    global mqtt_client

    command_id = payload.get("command_id")
    command_payload = payload.get("payload", {})

    logger.info(f"[MQTT] Executing command: {command_type} (id={command_id})")

    success, error, result = execute_command(command_type, command_payload)

    # Send acknowledgment via MQTT
    if mqtt_client:
        mqtt_client.publish_ack(command_id, success, error)

    if success:
        logger.info(f"[MQTT] Command {command_type} completed successfully")
    else:
        logger.warning(f"[MQTT] Command {command_type} failed: {error}")


def start_mqtt(config: AgentConfig) -> bool:
    """
    Initialize and start MQTT client if configured.

    Returns:
        True if MQTT started successfully (or not configured)
    """
    global mqtt_client

    if not config.mqtt_enabled or not config.mqtt_broker_url:
        logger.info("MQTT: disabled (no broker URL configured)")
        return True

    if not config.device_id or not config.organization_id:
        logger.warning(
            "MQTT: disabled (device not enrolled - missing device_id or organization_id)"
        )
        return True

    try:
        from valet_agent.mqtt import MqttClient, MqttConfig

        mqtt_config = MqttConfig(
            broker_url=config.mqtt_broker_url,
            org_id=config.organization_id,
            device_id=config.device_id,
            username=config.mqtt_username,
            password=config.mqtt_password,
            keepalive=config.mqtt_keepalive,
        )

        mqtt_client = MqttClient(mqtt_config)
        mqtt_client.on_command = handle_mqtt_command

        if mqtt_client.connect():
            logger.info(f"MQTT: connecting to {config.mqtt_broker_url}")
            return True
        else:
            logger.warning("MQTT: connection failed, falling back to polling mode")
            mqtt_client = None
            return True  # Don't fail startup, just use polling

    except ImportError as e:
        logger.warning(f"MQTT: disabled (paho-mqtt not installed: {e})")
        return True
    except Exception as e:
        logger.error(f"MQTT: failed to start: {e}")
        return True  # Don't fail startup


def stop_mqtt() -> None:
    """Stop MQTT client if running."""
    global mqtt_client

    if mqtt_client:
        mqtt_client.disconnect()
        mqtt_client = None


def run_checkin_loop(client: ValetClient, config: AgentConfig) -> None:
    """Main check-in loop."""
    global running

    while running:
        try:
            # Collect system information
            logger.debug("Collecting system information...")
            system_info = collect_system_info(
                include_packages=config.report_packages,
                include_services=config.report_services,
                include_location=config.beacondb_enabled and config.report_location,
                beacondb_url=config.beacondb_url,
                beacondb_timeout=config.beacondb_timeout,
            )

            # Log location if available
            if system_info.latitude and system_info.longitude:
                logger.info(
                    f"Location: {system_info.latitude:.6f}, {system_info.longitude:.6f} "
                    f"(source: {system_info.location_source}, accuracy: {system_info.location_accuracy}m)"
                )

            # Send check-in
            logger.info(f"Checking in with {config.server_url}...")
            response = client.checkin(system_info)

            # Update check-in interval if server specifies
            interval = response.get("next_checkin_seconds", config.checkin_interval_seconds)

            # Process any pending commands from HTTP response
            # (MQTT delivers commands in real-time, but HTTP is a fallback)
            commands = response.get("commands", [])
            for cmd in commands:
                cmd_id = cmd.get("id")
                cmd_type = cmd.get("command_type")
                payload = cmd.get("payload", {})

                logger.info(f"Executing command: {cmd_type} (id={cmd_id})")

                success, error, result = execute_command(cmd_type, payload)

                # Report result via HTTP
                client.report_command_result(
                    command_id=cmd_id,
                    success=success,
                    error_message=error,
                    result_data=result,
                )

                if success:
                    logger.info(f"Command {cmd_type} completed successfully")
                else:
                    logger.warning(f"Command {cmd_type} failed: {error}")

            mqtt_status = "connected" if mqtt_client and mqtt_client.connected else "disconnected"
            logger.info(f"Check-in complete. Next check-in in {interval}s (MQTT: {mqtt_status})")

        except Exception as e:
            logger.error(f"Check-in failed: {e}")
            interval = min(config.checkin_interval_seconds * 2, 600)  # Back off, max 10 min

        # Wait for next check-in (interruptible)
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)


def main() -> None:
    """Main entry point."""
    try:
        from importlib.metadata import version

        package_version = version("valet-agent")
    except Exception:
        package_version = "2025.01.12"

    print(f"🎩 DeviceValet Linux Agent v{package_version}")

    # Setup signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Load configuration
    config = load_config()

    if not config.auth_token:
        logger.error("No auth token configured. Run 'valet-agent enroll' first.")
        sys.exit(1)

    if not config.server_url:
        logger.error("No server URL configured.")
        sys.exit(1)

    logger.info(f"Server: {config.server_url}")
    logger.info(f"Check-in interval: {config.checkin_interval_seconds}s")

    if config.beacondb_enabled and config.report_location:
        logger.info(f"WiFi location: enabled (BeaconDB: {config.beacondb_url})")
    else:
        logger.info("WiFi location: disabled")

    # Create API client
    client = ValetClient(config)

    # Start MQTT for real-time commands (optional)
    start_mqtt(config)

    try:
        # Report startup event
        try:
            client.report_event(
                event_type="agent_started",
                message="DeviceValet Linux Agent started",
                severity="info",
            )
        except Exception:
            pass  # Don't fail on startup event

        # Run main loop
        run_checkin_loop(client, config)

    finally:
        stop_mqtt()
        client.close()
        logger.info("Agent stopped")


if __name__ == "__main__":
    main()
