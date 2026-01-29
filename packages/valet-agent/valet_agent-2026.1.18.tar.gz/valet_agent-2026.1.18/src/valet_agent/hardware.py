"""Detailed hardware information collector using DMI, sysfs, and system commands."""

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes for Hardware Information
# =============================================================================


@dataclass
class BiosInfo:
    """BIOS/UEFI firmware information."""

    vendor: str | None = None
    version: str | None = None
    release_date: str | None = None
    revision: str | None = None  # e.g., "5.19"


@dataclass
class SystemInfo:
    """System/motherboard information."""

    manufacturer: str | None = None
    product_name: str | None = None
    version: str | None = None
    serial_number: str | None = None
    uuid: str | None = None
    sku: str | None = None
    family: str | None = None


@dataclass
class BaseboardInfo:
    """Motherboard/baseboard information."""

    manufacturer: str | None = None
    product_name: str | None = None
    version: str | None = None
    serial_number: str | None = None
    asset_tag: str | None = None


@dataclass
class ChassisInfo:
    """Chassis/enclosure information."""

    manufacturer: str | None = None
    chassis_type: str | None = None  # e.g., "Desktop", "Notebook", "Server"
    version: str | None = None
    serial_number: str | None = None
    asset_tag: str | None = None


@dataclass
class CpuInfo:
    """Processor information."""

    model_name: str | None = None
    vendor: str | None = None
    architecture: str | None = None  # x86_64, aarch64, etc.
    physical_cores: int | None = None
    logical_cores: int | None = None
    threads_per_core: int | None = None
    sockets: int | None = None
    max_frequency_mhz: float | None = None
    current_frequency_mhz: float | None = None
    cache_l1d_kb: int | None = None
    cache_l1i_kb: int | None = None
    cache_l2_kb: int | None = None
    cache_l3_kb: int | None = None
    flags: list[str] = field(default_factory=list)
    virtualization: str | None = None  # vmx, svm, or None


@dataclass
class MemoryModule:
    """Individual memory module (DIMM) information."""

    locator: str | None = None  # e.g., "DIMM_A1"
    bank_locator: str | None = None
    size_mb: int | None = None
    form_factor: str | None = None  # e.g., "DIMM", "SODIMM"
    memory_type: str | None = None  # e.g., "DDR4", "DDR5"
    speed_mhz: int | None = None
    configured_speed_mhz: int | None = None
    manufacturer: str | None = None
    serial_number: str | None = None
    part_number: str | None = None
    rank: int | None = None


@dataclass
class MemoryInfo:
    """System memory information."""

    total_mb: int | None = None
    available_mb: int | None = None
    used_mb: int | None = None
    percent_used: float | None = None
    swap_total_mb: int | None = None
    swap_used_mb: int | None = None
    modules: list[MemoryModule] = field(default_factory=list)
    max_capacity_gb: int | None = None
    slots_used: int | None = None
    slots_total: int | None = None


@dataclass
class StorageDevice:
    """Storage device information."""

    name: str | None = None  # e.g., "sda", "nvme0n1"
    model: str | None = None
    serial: str | None = None
    size_gb: float | None = None
    device_type: str | None = None  # "SSD", "HDD", "NVMe"
    interface: str | None = None  # "SATA", "NVMe", "USB"
    rotational: bool | None = None  # True for HDD, False for SSD
    firmware: str | None = None
    smart_status: str | None = None  # "PASSED", "FAILED", or None
    temperature_c: int | None = None
    partitions: list[dict] = field(default_factory=list)


@dataclass
class NetworkInterface:
    """Network interface information."""

    name: str | None = None  # e.g., "eth0", "wlan0"
    mac_address: str | None = None
    ipv4_addresses: list[str] = field(default_factory=list)
    ipv6_addresses: list[str] = field(default_factory=list)
    speed_mbps: int | None = None
    mtu: int | None = None
    state: str | None = None  # "up", "down"
    interface_type: str | None = None  # "ethernet", "wifi", "loopback", "virtual"
    driver: str | None = None
    is_physical: bool = True


@dataclass
class GpuInfo:
    """Graphics processor information."""

    name: str | None = None
    vendor: str | None = None
    driver: str | None = None
    memory_mb: int | None = None
    pci_slot: str | None = None


@dataclass
class BatteryInfo:
    """Battery information (for laptops)."""

    present: bool = False
    status: str | None = None  # "Charging", "Discharging", "Full", "Not charging"
    percent: float | None = None
    time_remaining_minutes: int | None = None
    capacity_wh: float | None = None
    design_capacity_wh: float | None = None
    health_percent: float | None = None  # capacity / design_capacity
    manufacturer: str | None = None
    model: str | None = None
    serial: str | None = None
    technology: str | None = None  # "Li-ion", "Li-poly", etc.
    cycle_count: int | None = None


@dataclass
class OsInfo:
    """Operating system distribution information."""

    name: str | None = None  # e.g., "Arch Linux", "Ubuntu", "Debian"
    version: str | None = None  # e.g., "24.04", "12"
    version_codename: str | None = None  # e.g., "noble", "bookworm"
    id: str | None = None  # e.g., "arch", "ubuntu", "debian"
    id_like: list[str] = field(default_factory=list)  # e.g., ["debian"]
    pretty_name: str | None = None  # Human-readable name
    kernel_version: str | None = None  # e.g., "6.16.5-arch1-1"
    kernel_arch: str | None = None  # e.g., "x86_64"
    uptime_seconds: int | None = None
    boot_time: str | None = None  # ISO format


@dataclass
class ThermalSensor:
    """Temperature sensor reading."""

    label: str | None = None  # e.g., "CPU", "GPU", "nvme0"
    current_c: float | None = None
    high_c: float | None = None  # Warning threshold
    critical_c: float | None = None  # Critical threshold


@dataclass
class ProcessInfo:
    """Process information for top consumers."""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    user: str | None = None
    status: str | None = None


@dataclass
class DetailedHardwareInfo:
    """Complete detailed hardware information."""

    bios: BiosInfo = field(default_factory=BiosInfo)
    system: SystemInfo = field(default_factory=SystemInfo)
    baseboard: BaseboardInfo = field(default_factory=BaseboardInfo)
    chassis: ChassisInfo = field(default_factory=ChassisInfo)
    cpu: CpuInfo = field(default_factory=CpuInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    storage: list[StorageDevice] = field(default_factory=list)
    network: list[NetworkInterface] = field(default_factory=list)
    gpus: list[GpuInfo] = field(default_factory=list)
    battery: BatteryInfo | None = None
    os: OsInfo = field(default_factory=OsInfo)
    thermals: list[ThermalSensor] = field(default_factory=list)
    top_processes: list[ProcessInfo] = field(default_factory=list)


# =============================================================================
# DMI/SMBIOS Reading Functions
# =============================================================================


def _read_dmi_file(key: str) -> str | None:
    """Read a single DMI value from sysfs."""
    path = Path(f"/sys/class/dmi/id/{key}")
    try:
        if path.exists():
            value = path.read_text().strip()
            # Filter out placeholder values
            if value.lower() not in (
                "",
                "to be filled",
                "default string",
                "not specified",
                "n/a",
                "none",
            ):
                return value
    except (OSError, PermissionError) as e:
        logger.debug(f"Cannot read {path}: {e}")
    return None


def _run_dmidecode(type_num: int | None = None, string_key: str | None = None) -> str | None:
    """Run dmidecode and return output."""
    try:
        cmd = ["dmidecode"]
        if type_num is not None:
            cmd.extend(["-t", str(type_num)])
        elif string_key:
            cmd.extend(["-s", string_key])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError) as e:
        logger.debug(f"dmidecode failed: {e}")
    return None


def _parse_dmidecode_section(output: str, section_name: str) -> dict[str, str]:
    """Parse a dmidecode output section into key-value pairs."""
    result: dict[str, str] = {}
    in_section = False
    lines = output.split("\n")

    for line in lines:
        if section_name in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("Handle ") or (line.strip() == "" and result):
                break
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if value and value.lower() not in ("not specified", "to be filled", "n/a"):
                    result[key] = value

    return result


# =============================================================================
# Hardware Collection Functions
# =============================================================================


def collect_bios_info() -> BiosInfo:
    """Collect BIOS/UEFI information."""
    return BiosInfo(
        vendor=_read_dmi_file("bios_vendor"),
        version=_read_dmi_file("bios_version"),
        release_date=_read_dmi_file("bios_date"),
    )


def collect_system_info() -> SystemInfo:
    """Collect system information from DMI."""
    return SystemInfo(
        manufacturer=_read_dmi_file("sys_vendor"),
        product_name=_read_dmi_file("product_name"),
        version=_read_dmi_file("product_version"),
        serial_number=_read_dmi_file("product_serial"),
        uuid=_read_dmi_file("product_uuid"),
        sku=_read_dmi_file("product_sku"),
        family=_read_dmi_file("product_family"),
    )


def collect_baseboard_info() -> BaseboardInfo:
    """Collect motherboard information."""
    return BaseboardInfo(
        manufacturer=_read_dmi_file("board_vendor"),
        product_name=_read_dmi_file("board_name"),
        version=_read_dmi_file("board_version"),
        serial_number=_read_dmi_file("board_serial"),
        asset_tag=_read_dmi_file("board_asset_tag"),
    )


def collect_chassis_info() -> ChassisInfo:
    """Collect chassis information."""
    # Chassis type mapping from DMI spec
    chassis_types = {
        "1": "Other",
        "2": "Unknown",
        "3": "Desktop",
        "4": "Low Profile Desktop",
        "5": "Pizza Box",
        "6": "Mini Tower",
        "7": "Tower",
        "8": "Portable",
        "9": "Laptop",
        "10": "Notebook",
        "11": "Hand Held",
        "12": "Docking Station",
        "13": "All in One",
        "14": "Sub Notebook",
        "15": "Space-saving",
        "16": "Lunch Box",
        "17": "Main Server Chassis",
        "18": "Expansion Chassis",
        "19": "SubChassis",
        "20": "Bus Expansion Chassis",
        "21": "Peripheral Chassis",
        "22": "RAID Chassis",
        "23": "Rack Mount Chassis",
        "24": "Sealed-case PC",
        "25": "Multi-system chassis",
        "26": "Compact PCI",
        "27": "Advanced TCA",
        "28": "Blade",
        "29": "Blade Enclosure",
        "30": "Tablet",
        "31": "Convertible",
        "32": "Detachable",
        "33": "IoT Gateway",
        "34": "Embedded PC",
        "35": "Mini PC",
        "36": "Stick PC",
    }

    chassis_type_num = _read_dmi_file("chassis_type")
    chassis_type = (
        chassis_types.get(chassis_type_num, chassis_type_num) if chassis_type_num else None
    )

    return ChassisInfo(
        manufacturer=_read_dmi_file("chassis_vendor"),
        chassis_type=chassis_type,
        version=_read_dmi_file("chassis_version"),
        serial_number=_read_dmi_file("chassis_serial"),
        asset_tag=_read_dmi_file("chassis_asset_tag"),
    )


def collect_cpu_info() -> CpuInfo:
    """Collect detailed CPU information."""
    info = CpuInfo()

    # Read /proc/cpuinfo for detailed info
    cpuinfo_path = Path("/proc/cpuinfo")
    if cpuinfo_path.exists():
        content = cpuinfo_path.read_text()

        # Extract model name
        match = re.search(r"model name\s*:\s*(.+)", content)
        if match:
            info.model_name = match.group(1).strip()

        # Extract vendor
        match = re.search(r"vendor_id\s*:\s*(.+)", content)
        if match:
            info.vendor = match.group(1).strip()

        # Extract flags
        match = re.search(r"flags\s*:\s*(.+)", content)
        if match:
            info.flags = match.group(1).strip().split()
            # Check for virtualization support
            if "vmx" in info.flags:
                info.virtualization = "vmx"  # Intel VT-x
            elif "svm" in info.flags:
                info.virtualization = "svm"  # AMD-V

    # Use lscpu for structured info
    try:
        result = subprocess.run(["lscpu", "-J"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            lscpu = {item["field"].rstrip(":"): item["data"] for item in data.get("lscpu", [])}

            info.architecture = lscpu.get("Architecture")
            info.sockets = _safe_int(lscpu.get("Socket(s)"))
            info.physical_cores = _safe_int(lscpu.get("Core(s) per socket"))
            if info.sockets and info.physical_cores:
                info.physical_cores *= info.sockets
            info.logical_cores = _safe_int(lscpu.get("CPU(s)"))
            info.threads_per_core = _safe_int(lscpu.get("Thread(s) per core"))

            # Frequency
            max_freq = lscpu.get("CPU max MHz")
            if max_freq:
                info.max_frequency_mhz = float(max_freq)

            # Cache sizes
            for cache_line in ["L1d cache", "L1i cache", "L2 cache", "L3 cache"]:
                if cache_line in lscpu:
                    value = lscpu[cache_line]
                    size_kb = _parse_cache_size(value)
                    if "L1d" in cache_line:
                        info.cache_l1d_kb = size_kb
                    elif "L1i" in cache_line:
                        info.cache_l1i_kb = size_kb
                    elif "L2" in cache_line:
                        info.cache_l2_kb = size_kb
                    elif "L3" in cache_line:
                        info.cache_l3_kb = size_kb

    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        logger.debug(f"lscpu failed: {e}")

    # Current frequency from psutil
    freq = psutil.cpu_freq()
    if freq:
        info.current_frequency_mhz = freq.current

    return info


def collect_memory_info() -> MemoryInfo:
    """Collect detailed memory information."""
    info = MemoryInfo()

    # Basic memory stats from psutil
    mem = psutil.virtual_memory()
    info.total_mb = round(mem.total / (1024 * 1024))
    info.available_mb = round(mem.available / (1024 * 1024))
    info.used_mb = round(mem.used / (1024 * 1024))
    info.percent_used = mem.percent

    swap = psutil.swap_memory()
    info.swap_total_mb = round(swap.total / (1024 * 1024))
    info.swap_used_mb = round(swap.used / (1024 * 1024))

    # Detailed DIMM info from dmidecode
    output = _run_dmidecode(type_num=17)  # Memory Device
    if output:
        # Parse memory modules
        modules = []
        current_module: dict[str, Any] = {}

        for line in output.split("\n"):
            if "Memory Device" in line and "Handle" in line:
                if current_module and current_module.get("Size"):
                    modules.append(current_module)
                current_module = {}
            elif ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if value and value.lower() not in (
                    "unknown",
                    "not specified",
                    "no module installed",
                ):
                    current_module[key] = value

        if current_module and current_module.get("Size"):
            modules.append(current_module)

        # Convert to MemoryModule objects
        for mod in modules:
            size_str = mod.get("Size", "")
            size_mb = None
            if "MB" in size_str:
                size_mb = _safe_int(size_str.replace("MB", "").strip())
            elif "GB" in size_str:
                size_mb = _safe_int(size_str.replace("GB", "").strip())
                if size_mb:
                    size_mb *= 1024

            if size_mb:  # Only add populated slots
                info.modules.append(
                    MemoryModule(
                        locator=mod.get("Locator"),
                        bank_locator=mod.get("Bank Locator"),
                        size_mb=size_mb,
                        form_factor=mod.get("Form Factor"),
                        memory_type=mod.get("Type"),
                        speed_mhz=_safe_int(
                            mod.get("Speed", "").replace("MT/s", "").replace("MHz", "").strip()
                        ),
                        configured_speed_mhz=_safe_int(
                            mod.get("Configured Memory Speed", "")
                            .replace("MT/s", "")
                            .replace("MHz", "")
                            .strip()
                        ),
                        manufacturer=mod.get("Manufacturer"),
                        serial_number=mod.get("Serial Number"),
                        part_number=mod.get("Part Number"),
                        rank=_safe_int(mod.get("Rank")),
                    )
                )

        info.slots_used = len(info.modules)

    # Physical Memory Array info (max capacity, slots)
    output = _run_dmidecode(type_num=16)
    if output:
        match = re.search(r"Maximum Capacity:\s*(\d+)\s*(GB|TB)", output)
        if match:
            capacity = int(match.group(1))
            if match.group(2) == "TB":
                capacity *= 1024
            info.max_capacity_gb = capacity

        match = re.search(r"Number Of Devices:\s*(\d+)", output)
        if match:
            info.slots_total = int(match.group(1))

    return info


def collect_storage_info() -> list[StorageDevice]:
    """Collect information about all storage devices."""
    devices = []

    # Get block devices from lsblk
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,MODEL,SERIAL,ROTA,TRAN,MOUNTPOINT,FSTYPE"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)

            for dev in data.get("blockdevices", []):
                if dev.get("type") != "disk":
                    continue

                name = dev.get("name")
                size_bytes = _safe_int(dev.get("size"))
                size_gb = round(size_bytes / (1024**3), 2) if size_bytes else None

                rotational = dev.get("rota")
                transport = dev.get("tran", "").upper()

                # Determine device type
                if transport == "NVME":
                    device_type = "NVMe"
                    interface = "NVMe"
                elif rotational == "0" or rotational is False:
                    device_type = "SSD"
                    interface = transport or "SATA"
                else:
                    device_type = "HDD"
                    interface = transport or "SATA"

                # Get partitions
                partitions = []
                for child in dev.get("children", []):
                    if child.get("type") == "part":
                        part_size = _safe_int(child.get("size"))
                        partitions.append(
                            {
                                "name": child.get("name"),
                                "size_gb": round(part_size / (1024**3), 2) if part_size else None,
                                "mountpoint": child.get("mountpoint"),
                                "fstype": child.get("fstype"),
                            }
                        )

                storage_dev = StorageDevice(
                    name=name,
                    model=dev.get("model", "").strip() if dev.get("model") else None,
                    serial=dev.get("serial"),
                    size_gb=size_gb,
                    device_type=device_type,
                    interface=interface,
                    rotational=rotational == "1" or rotational is True,
                    partitions=partitions,
                )

                # Try to get SMART status
                smart_info = _get_smart_info(f"/dev/{name}")
                if smart_info:
                    storage_dev.smart_status = smart_info.get("status")
                    storage_dev.temperature_c = smart_info.get("temperature")
                    if not storage_dev.firmware:
                        storage_dev.firmware = smart_info.get("firmware")

                devices.append(storage_dev)

    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        logger.debug(f"lsblk failed: {e}")

    return devices


def _get_smart_info(device: str) -> dict | None:
    """Get SMART status for a device."""
    try:
        result = subprocess.run(
            ["smartctl", "-H", "-A", "-i", device], capture_output=True, text=True, timeout=10
        )
        info: dict[str, str | int] = {}

        # Parse health status
        if "PASSED" in result.stdout:
            info["status"] = "PASSED"
        elif "FAILED" in result.stdout:
            info["status"] = "FAILED"

        # Parse temperature
        temp_match = re.search(r"Temperature.*?(\d+)\s*(?:Celsius|C)", result.stdout, re.IGNORECASE)
        if temp_match:
            info["temperature"] = int(temp_match.group(1))

        # Parse firmware
        fw_match = re.search(r"Firmware Version:\s*(\S+)", result.stdout)
        if fw_match:
            info["firmware"] = fw_match.group(1)

        return info if info else None

    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return None


def collect_network_info() -> list[NetworkInterface]:
    """Collect information about all network interfaces."""
    interfaces = []

    # Get interface stats from psutil
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    for iface_name, iface_stats in stats.items():
        iface = NetworkInterface(
            name=iface_name,
            speed_mbps=iface_stats.speed if iface_stats.speed > 0 else None,
            mtu=iface_stats.mtu,
            state="up" if iface_stats.isup else "down",
        )

        # Determine interface type
        if iface_name.startswith("lo"):
            iface.interface_type = "loopback"
            iface.is_physical = False
        elif iface_name.startswith(("wl", "wlan", "wifi")):
            iface.interface_type = "wifi"
        elif iface_name.startswith(("en", "eth")):
            iface.interface_type = "ethernet"
        elif iface_name.startswith(("br", "virbr")):
            iface.interface_type = "bridge"
            iface.is_physical = False
        elif iface_name.startswith(("veth", "docker")):
            iface.interface_type = "virtual"
            iface.is_physical = False
        elif iface_name.startswith(("tun", "tap", "wg")):
            iface.interface_type = "tunnel"
            iface.is_physical = False
        else:
            iface.interface_type = "other"

        # Get addresses
        if iface_name in addrs:
            for addr in addrs[iface_name]:
                if addr.family == psutil.AF_LINK:
                    iface.mac_address = addr.address
                elif addr.family.name == "AF_INET":
                    iface.ipv4_addresses.append(addr.address)
                elif addr.family.name == "AF_INET6":
                    # Skip link-local addresses
                    if not addr.address.startswith("fe80:"):
                        iface.ipv6_addresses.append(addr.address)

        # Get driver info from sysfs
        driver_path = Path(f"/sys/class/net/{iface_name}/device/driver")
        if driver_path.is_symlink():
            iface.driver = driver_path.resolve().name

        interfaces.append(iface)

    return interfaces


def collect_gpu_info() -> list[GpuInfo]:
    """Collect GPU information."""
    gpus = []

    # Try lspci for GPU detection
    try:
        result = subprocess.run(["lspci", "-v", "-nn"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Split into device blocks (separated by blank lines)
            blocks = result.stdout.split("\n\n")

            for block in blocks:
                if "VGA compatible controller" not in block and "3D controller" not in block:
                    continue

                lines = block.strip().split("\n")
                if not lines:
                    continue

                gpu_info: dict[str, Any] = {}

                # First line contains PCI slot and device name
                first_line = lines[0]
                match = re.match(r"(\S+)\s+(?:VGA|3D)[^:]+:\s+(.+)", first_line)
                if match:
                    gpu_info["pci_slot"] = match.group(1)
                    full_name = match.group(2)

                    # Clean up the name - extract the actual GPU name
                    # Format: "Vendor Name [Vendor ID:Device ID] (rev XX)"
                    name_match = re.match(
                        r"(.+?)\s*\[[\da-f]{4}:[\da-f]{4}\]", full_name, re.IGNORECASE
                    )
                    if name_match:
                        gpu_info["name"] = name_match.group(1).strip()
                    else:
                        gpu_info["name"] = full_name.split("(rev")[0].strip()

                    # Extract vendor
                    if "NVIDIA" in full_name.upper():
                        gpu_info["vendor"] = "NVIDIA"
                    elif "AMD" in full_name.upper() or "ATI" in full_name.upper():
                        gpu_info["vendor"] = "AMD"
                    elif "INTEL" in full_name.upper():
                        gpu_info["vendor"] = "Intel"

                # Parse remaining lines for driver info
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith("Kernel driver in use:"):
                        gpu_info["driver"] = line.split(":", 1)[-1].strip()
                    elif line.startswith("Memory at") and "prefetchable" in line:
                        # Try to parse memory size from BAR
                        mem_match = re.search(r"\[size=(\d+)(M|G)\]", line)
                        if mem_match:
                            size = int(mem_match.group(1))
                            if mem_match.group(2) == "G":
                                size *= 1024
                            gpu_info["memory_mb"] = size

                if gpu_info.get("name"):
                    gpus.append(GpuInfo(**gpu_info))

    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.debug(f"lspci failed: {e}")

    return gpus


def collect_os_info() -> OsInfo:
    """Collect OS distribution and kernel information."""
    import platform
    from datetime import datetime, timezone

    info = OsInfo()

    # Kernel info
    info.kernel_version = platform.release()
    info.kernel_arch = platform.machine()

    # Uptime
    boot_time = psutil.boot_time()
    info.uptime_seconds = int(datetime.now().timestamp() - boot_time)
    info.boot_time = datetime.fromtimestamp(boot_time, tz=timezone.utc).isoformat()

    # Parse /etc/os-release for distribution info
    os_release_path = Path("/etc/os-release")
    if os_release_path.exists():
        os_release = {}
        for line in os_release_path.read_text().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                # Remove quotes from value
                value = value.strip("\"'")
                os_release[key] = value

        info.name = os_release.get("NAME")
        info.version = os_release.get("VERSION_ID")
        info.version_codename = os_release.get("VERSION_CODENAME")
        info.id = os_release.get("ID")
        info.pretty_name = os_release.get("PRETTY_NAME")

        # ID_LIKE can be space-separated
        id_like = os_release.get("ID_LIKE", "")
        if id_like:
            info.id_like = id_like.split()

    return info


def collect_thermal_info() -> list[ThermalSensor]:
    """Collect temperature sensor readings."""
    sensors: list[ThermalSensor] = []

    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return sensors

        for chip_name, chip_temps in temps.items():
            for temp in chip_temps:
                # Create a meaningful label
                if temp.label:
                    label = f"{chip_name}/{temp.label}"
                else:
                    label = chip_name

                # Skip sensors with no reading
                if temp.current is None or temp.current == 0:
                    continue

                sensors.append(
                    ThermalSensor(
                        label=label,
                        current_c=round(temp.current, 1),
                        high_c=round(temp.high, 1) if temp.high else None,
                        critical_c=round(temp.critical, 1) if temp.critical else None,
                    )
                )

    except (AttributeError, NotImplementedError):
        # sensors_temperatures not available on this platform
        pass

    # Also check NVMe drives via sysfs
    for nvme_path in Path("/sys/class/nvme").glob("nvme*"):
        temp_path = nvme_path / "hwmon"
        if temp_path.exists():
            for hwmon in temp_path.iterdir():
                temp_input = hwmon / "temp1_input"
                if temp_input.exists():
                    try:
                        temp_mc = int(temp_input.read_text().strip())
                        nvme_name = nvme_path.name
                        sensors.append(
                            ThermalSensor(
                                label=f"nvme/{nvme_name}",
                                current_c=round(temp_mc / 1000, 1),
                            )
                        )
                    except (ValueError, OSError):
                        pass

    return sensors


def collect_top_processes(limit: int = 10) -> list[ProcessInfo]:
    """Collect top processes by CPU and memory usage."""
    processes = []

    # First pass to initialize CPU percent (requires interval)
    for _proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
        pass

    # Small delay to get meaningful CPU readings
    import time

    time.sleep(0.1)

    # Second pass to collect data
    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent", "memory_info", "username", "status"]
    ):
        try:
            pinfo = proc.info
            if pinfo["pid"] == 0:  # Skip kernel
                continue

            memory_mb = 0
            if pinfo.get("memory_info"):
                memory_mb = pinfo["memory_info"].rss / (1024 * 1024)

            processes.append(
                ProcessInfo(
                    pid=pinfo["pid"],
                    name=pinfo["name"] or "unknown",
                    cpu_percent=pinfo.get("cpu_percent") or 0,
                    memory_percent=pinfo.get("memory_percent") or 0,
                    memory_mb=round(memory_mb, 1),
                    user=pinfo.get("username"),
                    status=pinfo.get("status"),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Sort by CPU + memory usage combined, take top N
    processes.sort(key=lambda p: p.cpu_percent + p.memory_percent, reverse=True)
    return processes[:limit]


def collect_battery_info() -> BatteryInfo | None:
    """Collect battery information for laptops."""
    battery = psutil.sensors_battery()
    if not battery:
        return None

    info = BatteryInfo(present=True)
    info.percent = battery.percent

    if battery.power_plugged:
        if battery.percent >= 100:
            info.status = "Full"
        else:
            info.status = "Charging"
    else:
        info.status = "Discharging"

    if battery.secsleft > 0:
        info.time_remaining_minutes = battery.secsleft // 60

    # Try to get detailed battery info from sysfs
    bat_paths = list(Path("/sys/class/power_supply").glob("BAT*"))
    if bat_paths:
        bat_path = bat_paths[0]

        # Read various battery attributes
        def read_bat(name: str) -> str | None:
            try:
                return (bat_path / name).read_text().strip()
            except (OSError, FileNotFoundError):
                return None

        info.manufacturer = read_bat("manufacturer")
        info.model = read_bat("model_name")
        info.serial = read_bat("serial_number")
        info.technology = read_bat("technology")

        # Capacity calculations
        energy_full = _safe_int(read_bat("energy_full"))
        energy_full_design = _safe_int(read_bat("energy_full_design"))

        if energy_full:
            info.capacity_wh = energy_full / 1000000  # Convert from µWh
        if energy_full_design:
            info.design_capacity_wh = energy_full_design / 1000000

        if energy_full and energy_full_design:
            info.health_percent = round((energy_full / energy_full_design) * 100, 1)

        cycle_count = read_bat("cycle_count")
        if cycle_count:
            info.cycle_count = _safe_int(cycle_count)

    return info


# =============================================================================
# Helper Functions
# =============================================================================


def _safe_int(value: Any) -> int | None:
    """Safely convert a value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_cache_size(value: str) -> int | None:
    """Parse cache size string to KB."""
    if not value:
        return None

    value = value.strip().upper()
    match = re.match(r"(\d+(?:\.\d+)?)\s*(K|M|G)?I?B?", value)
    if match:
        num = float(match.group(1))
        unit = match.group(2) or "K"
        if unit == "M":
            return int(num * 1024)
        elif unit == "G":
            return int(num * 1024 * 1024)
        return int(num)
    return None


# =============================================================================
# Main Collection Function
# =============================================================================


def collect_detailed_hardware_info(
    include_processes: bool = True,
    process_limit: int = 10,
) -> DetailedHardwareInfo:
    """
    Collect all detailed hardware information.

    Args:
        include_processes: Whether to collect top process info (adds ~100ms delay)
        process_limit: Max number of processes to include
    """
    return DetailedHardwareInfo(
        bios=collect_bios_info(),
        system=collect_system_info(),
        baseboard=collect_baseboard_info(),
        chassis=collect_chassis_info(),
        cpu=collect_cpu_info(),
        memory=collect_memory_info(),
        storage=collect_storage_info(),
        network=collect_network_info(),
        gpus=collect_gpu_info(),
        battery=collect_battery_info(),
        os=collect_os_info(),
        thermals=collect_thermal_info(),
        top_processes=collect_top_processes(process_limit) if include_processes else [],
    )


def hardware_info_to_dict(info: DetailedHardwareInfo) -> dict:
    """Convert DetailedHardwareInfo to a dictionary for JSON serialization."""
    from dataclasses import asdict

    return asdict(info)
