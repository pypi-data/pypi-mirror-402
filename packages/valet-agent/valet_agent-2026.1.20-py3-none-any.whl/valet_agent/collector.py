"""System information collector for Linux devices."""

import logging
import platform
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psutil

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class SystemInfo:
    """Collected system information."""

    # Hardware
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None

    # OS
    os_version: str | None = None
    hostname: str | None = None

    # Health
    storage_total_gb: float | None = None
    storage_free_gb: float | None = None
    memory_total_mb: int | None = None
    memory_free_mb: int | None = None
    uptime_seconds: int | None = None
    cpu_percent: float | None = None

    # Network
    ip_address: str | None = None
    mac_address: str | None = None
    connection_type: str = "ethernet"

    # Location (WiFi-based via BeaconDB)
    latitude: float | None = None
    longitude: float | None = None
    location_source: str | None = None  # wifi, ip
    location_accuracy: float | None = None  # Accuracy in meters

    # Platform-specific
    platform_data: dict | None = None


def get_dmi_info(key: str) -> str | None:
    """Read DMI/SMBIOS information."""
    path = Path(f"/sys/class/dmi/id/{key}")
    try:
        if path.exists():
            return path.read_text().strip()
    except (OSError, PermissionError):
        pass
    return None


def get_serial_number() -> str | None:
    """Get system serial number."""
    # Try DMI first
    serial = get_dmi_info("product_serial")
    if serial and serial.lower() not in ("", "to be filled", "default string", "not specified"):
        return serial

    # Try dmidecode
    try:
        result = subprocess.run(
            ["dmidecode", "-s", "system-serial-number"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            serial = result.stdout.strip()
            if serial and serial.lower() not in ("", "to be filled", "not specified"):
                return serial
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback to machine-id
    machine_id_path = Path("/etc/machine-id")
    if machine_id_path.exists():
        return f"machine-{machine_id_path.read_text().strip()[:12]}"

    return None


def get_primary_ip() -> tuple[str | None, str | None]:
    """Get primary IP address and MAC address."""
    try:
        # Create a socket to determine the primary interface
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]

        # Find the interface with this IP to get its MAC
        for _iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address == ip_address:
                    # Found the interface, now get its MAC
                    for mac_addr in addrs:
                        if mac_addr.family == psutil.AF_LINK:
                            return ip_address, mac_addr.address

        return ip_address, None
    except OSError:
        return None, None


def get_installed_packages() -> list[dict]:
    """Get list of installed packages."""
    packages = []

    # Try dpkg (Debian/Ubuntu)
    try:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package}|${Version}\n"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    name, version = line.split("|", 1)
                    packages.append({"name": name, "version": version, "manager": "dpkg"})
            return packages
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try pacman (Arch)
    try:
        result = subprocess.run(
            ["pacman", "-Q"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    packages.append({"name": parts[0], "version": parts[1], "manager": "pacman"})
            return packages
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return packages


def get_running_services() -> list[dict]:
    """Get list of running systemd services."""
    services = []
    try:
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--state=running",
                "--no-pager",
                "--plain",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n")[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 1 and parts[0].endswith(".service"):
                    services.append(
                        {
                            "name": parts[0].replace(".service", ""),
                            "state": "running",
                        }
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return services


def get_wifi_location(
    beacondb_url: str = "https://api.beacondb.net",
    timeout: float = 5.0,
) -> tuple[float | None, float | None, str | None, float | None]:
    """
    Get location via WiFi using BeaconDB.

    Returns:
        Tuple of (latitude, longitude, source, accuracy) or (None, None, None, None)
    """
    try:
        from valet_agent.beacondb import BeaconDbClient
        from valet_agent.wifi import scan_wifi

        # Scan WiFi networks
        wifi_networks = scan_wifi()
        if not wifi_networks:
            logger.debug("No WiFi networks found for location")
            return None, None, None, None

        logger.debug(f"Found {len(wifi_networks)} WiFi networks, querying BeaconDB")

        # Query BeaconDB
        client = BeaconDbClient(base_url=beacondb_url, timeout=timeout)
        try:
            result = client.geolocate(wifi_networks)
            if result:
                logger.info(
                    f"WiFi location: {result.latitude}, {result.longitude} "
                    f"(acc: {result.accuracy}m, source: {result.source.value})"
                )
                return result.latitude, result.longitude, result.source.value, result.accuracy
        finally:
            client.close()

    except ImportError as e:
        logger.debug(f"BeaconDB modules not available: {e}")
    except Exception as e:
        logger.warning(f"WiFi location lookup failed: {e}")

    return None, None, None, None


def get_detailed_hardware_dict(include_processes: bool = False) -> dict:
    """
    Get detailed hardware information as a dictionary.

    This provides enhanced telemetry beyond basic check-in fields:
    - OS distribution details
    - CPU model, cores, frequency
    - GPU info
    - Network interfaces (all interfaces with IPs, MACs, speeds, drivers)
    - Thermal sensor readings
    - Optional top processes

    Args:
        include_processes: Include top 5 processes (adds ~100ms delay)

    Returns:
        Dictionary suitable for platform_data in check-ins
    """
    from valet_agent.hardware import (
        collect_cpu_info,
        collect_gpu_info,
        collect_network_info,
        collect_os_info,
        collect_thermal_info,
        collect_top_processes,
    )

    hw: dict[str, Any] = {}

    # OS distribution
    os_info = collect_os_info()
    hw["os"] = {
        "distro": os_info.pretty_name or os_info.name,
        "distro_id": os_info.id,
        "distro_like": os_info.id_like,
        "version": os_info.version,
        "codename": os_info.version_codename,
        "kernel": os_info.kernel_version,
        "arch": os_info.kernel_arch,
        "uptime_seconds": os_info.uptime_seconds,
        "boot_time": os_info.boot_time,
    }

    # CPU details
    cpu_info = collect_cpu_info()
    hw["cpu"] = {
        "model": cpu_info.model_name,
        "vendor": cpu_info.vendor,
        "arch": cpu_info.architecture,
        "cores_physical": cpu_info.physical_cores,
        "cores_logical": cpu_info.logical_cores,
        "threads_per_core": cpu_info.threads_per_core,
        "frequency_mhz": cpu_info.current_frequency_mhz,
        "frequency_max_mhz": cpu_info.max_frequency_mhz,
        "cache_l3_kb": cpu_info.cache_l3_kb,
        "virtualization": cpu_info.virtualization,
    }

    # GPUs
    gpus = collect_gpu_info()
    if gpus:
        hw["gpus"] = [
            {
                "name": gpu.name,
                "vendor": gpu.vendor,
                "driver": gpu.driver,
                "memory_mb": gpu.memory_mb,
            }
            for gpu in gpus
        ]

    # Network interfaces (all interfaces with detailed info)
    interfaces = collect_network_info()
    if interfaces:
        hw["network_interfaces"] = [
            {
                "name": iface.name,
                "type": iface.interface_type,
                "state": iface.state,
                "mac_address": iface.mac_address,
                "ipv4_addresses": iface.ipv4_addresses,
                "ipv6_addresses": iface.ipv6_addresses,
                "speed_mbps": iface.speed_mbps,
                "mtu": iface.mtu,
                "driver": iface.driver,
                "is_physical": iface.is_physical,
            }
            for iface in interfaces
            # Include all interfaces except loopback
            if iface.interface_type != "loopback"
        ]

    # Thermal sensors (only report non-trivial temps)
    thermals = collect_thermal_info()
    if thermals:
        hw["thermals"] = [
            {
                "label": t.label,
                "temp_c": t.current_c,
                "warn_c": t.high_c,
                "crit_c": t.critical_c,
            }
            for t in thermals
            if t.current_c and t.current_c > 0  # Skip zero readings
        ]

    # Top processes (optional, for diagnostics)
    if include_processes:
        processes = collect_top_processes(limit=5)
        hw["top_processes"] = [
            {
                "pid": p.pid,
                "name": p.name,
                "cpu_pct": round(p.cpu_percent, 1),
                "mem_pct": round(p.memory_percent, 1),
                "mem_mb": round(p.memory_mb, 0),
                "user": p.user,
            }
            for p in processes
        ]

    return hw


def collect_system_info(
    include_packages: bool = True,
    include_services: bool = True,
    include_location: bool = True,
    include_detailed_hardware: bool = True,
    beacondb_url: str = "https://api.beacondb.net",
    beacondb_timeout: float = 5.0,
) -> SystemInfo:
    """Collect all system information."""
    # Basic info
    ip_address, mac_address = get_primary_ip()

    # Memory
    mem = psutil.virtual_memory()

    # Disk
    disk = psutil.disk_usage("/")

    # Platform data - combines standard info with detailed hardware
    platform_data: dict[str, Any] = {}
    if include_packages:
        platform_data["installed_packages"] = get_installed_packages()
    if include_services:
        platform_data["running_services"] = get_running_services()
    if include_detailed_hardware:
        try:
            platform_data["hardware"] = get_detailed_hardware_dict(include_processes=False)
        except Exception as e:
            logger.warning(f"Failed to collect detailed hardware: {e}")

    # Location (WiFi-based via BeaconDB)
    latitude, longitude, location_source, location_accuracy = (None, None, None, None)
    if include_location:
        latitude, longitude, location_source, location_accuracy = get_wifi_location(
            beacondb_url=beacondb_url,
            timeout=beacondb_timeout,
        )

    return SystemInfo(
        manufacturer=get_dmi_info("sys_vendor"),
        model=get_dmi_info("product_name"),
        serial_number=get_serial_number(),
        os_version=f"{platform.system()} {platform.release()}",
        hostname=socket.gethostname(),
        storage_total_gb=round(disk.total / (1024**3), 2),
        storage_free_gb=round(disk.free / (1024**3), 2),
        memory_total_mb=round(mem.total / (1024**2)),
        memory_free_mb=round(mem.available / (1024**2)),
        uptime_seconds=int(time.time() - psutil.boot_time()),
        cpu_percent=psutil.cpu_percent(interval=1),
        ip_address=ip_address,
        mac_address=mac_address,
        connection_type="ethernet",
        latitude=latitude,
        longitude=longitude,
        location_source=location_source,
        location_accuracy=location_accuracy,
        platform_data=platform_data if platform_data else None,
    )
