"""Command-line interface for DeviceValet Linux Agent."""

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Version from package metadata
try:
    from importlib.metadata import version

    __version__ = version("valet-agent")
except Exception:
    __version__ = "2026.01.18"


def parse_activation_url(url: str) -> tuple[str, str]:
    """Parse activation URL to extract server and token.

    Supported URL formats:
    - Path-based:  https://valet.example.com/enroll/abc123
    - Query param: https://valet.example.com/enroll?token=abc123
    - API path:    https://valet.example.com/api/v1/enrollments/public/abc123
    - Raw token:   abc123 (with separate --server flag)

    Returns:
        Tuple of (server_url, token)

    Raises:
        ValueError: If URL is invalid or missing token
    """
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL: must include scheme (https://)")

    # Extract server base URL
    server_url = f"{parsed.scheme}://{parsed.netloc}"

    # Try query parameter first (legacy format)
    params = parse_qs(parsed.query)
    token = params.get("token", [None])[0]

    # Try path-based format if no query param
    if not token and parsed.path:
        # Handle paths like /enroll/abc123 or /api/v1/enrollments/public/abc123
        path_parts = parsed.path.strip("/").split("/")
        if path_parts:
            # Token is the last path segment (after 'enroll' or 'public')
            last_segment = path_parts[-1]
            # Validate it looks like a token (alphanumeric, dashes, underscores)
            if (
                last_segment
                and len(last_segment) >= 16
                and last_segment not in ("enroll", "public")
            ):
                token = last_segment

    if not token:
        raise ValueError(
            "Activation URL missing token. Expected format:\n"
            "  https://server/enroll/<token>  (path-based)\n"
            "  https://server/enroll?token=<token>  (query param)"
        )

    return server_url, token


def cmd_enroll(args: argparse.Namespace) -> int:
    """Enroll this device with the DeviceValet server.

    Credential sources (in priority order):
    1. --url flag (activation URL)
    2. VALET_ACTIVATION_URL environment variable
    3. --server and --token flags
    4. VALET_SERVER_URL and VALET_ENROLLMENT_TOKEN environment variables
    5. Interactive prompt (if TTY available)
    """
    from valet_agent.config import get_default_paths
    from valet_agent.enrollment import enroll_device

    print(f"🎩 DeviceValet Linux Agent v{__version__}")
    print()

    server_url: str | None = None
    token: str | None = None

    # Priority 1: Activation URL from --url flag
    if args.url:
        try:
            server_url, token = parse_activation_url(args.url)
            print("📋 Parsed activation URL (from --url)")
        except ValueError as e:
            print(f"❌ Invalid activation URL: {e}")
            return 1

    # Priority 2: Activation URL from environment variable
    if not server_url:
        env_url = os.environ.get("VALET_ACTIVATION_URL")
        if env_url:
            try:
                server_url, token = parse_activation_url(env_url)
                print("📋 Parsed activation URL (from VALET_ACTIVATION_URL)")
            except ValueError as e:
                print(f"❌ Invalid VALET_ACTIVATION_URL: {e}")
                return 1

    # Priority 3: Explicit --server and --token flags
    if not server_url:
        server_url = args.server
    if not token:
        token = args.token

    # Priority 4: Environment variables for server/token separately
    if not server_url:
        server_url = os.environ.get("VALET_SERVER_URL")
    if not token:
        token = os.environ.get("VALET_ENROLLMENT_TOKEN")

    # Priority 5: Interactive prompt if still missing and TTY available
    if not server_url and not token and sys.stdin.isatty():
        print("Enter the activation URL from your DeviceValet dashboard:")
        print("(Found at: Dashboard → Devices → Add Device → Linux)")
        print()
        try:
            url_input = input("Activation URL: ").strip()
            if url_input:
                try:
                    server_url, token = parse_activation_url(url_input)
                except ValueError as e:
                    print(f"❌ Invalid URL: {e}")
                    return 1
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Enrollment cancelled")
            return 1

    # Validate we have what we need
    if not server_url:
        print("❌ Error: Server URL required.")
        print("   Use --url with activation URL from dashboard")
        print("   Or use --server and --token separately")
        return 1

    if not token:
        print("❌ Error: Enrollment token required.")
        print("   Use --url with activation URL from dashboard")
        print("   Or use --token with enrollment token")
        return 1

    # Config path - use smart defaults or override
    if args.config_dir:
        config_dir = Path(args.config_dir)
    else:
        config_dir = get_default_paths()["config_dir"]
    config_file = config_dir / "agent.env"

    print(f"📡 Server: {server_url}")
    print(f"📁 Config: {config_file}")
    print()

    try:
        result = enroll_device(
            server_url=server_url,
            token=token,
            config_dir=config_dir,
            mqtt_url=args.mqtt_url,
        )

        if result["success"]:
            print("✅ Enrollment successful!")
            print()
            print(f"   Device ID: {result['device_id']}")
            print(f"   Device Name: {result['device_name']}")
            print(f"   Organization: {result['organization_name']}")
            print()
            print(f"📝 Configuration saved to: {config_file}")
            print()
            # Show appropriate next steps based on user context
            if os.getuid() == 0:
                print("Next steps:")
                print("  1. Start the agent:  systemctl start valet-agent")
                print("  2. Enable on boot:   systemctl enable valet-agent")
                print("  3. Check status:     valet-agent status")
            else:
                print("Next steps:")
                print("  1. Run the agent:    valet-agent run")
                print("  2. Check status:     valet-agent status")
                print()
                print("For system service (requires root):")
                print("  sudo valet-agent enroll --url '<activation-url>'")
            return 0
        else:
            print(f"❌ Enrollment failed: {result['error']}")
            return 1

    except PermissionError:
        print(f"❌ Permission denied writing to {config_file}")
        if os.getuid() != 0:
            print("   Try running with sudo for system-wide install:")
            print(f"   sudo valet-agent enroll --url '{args.url or '<activation-url>'}'")
        return 1
    except Exception as e:
        print(f"❌ Enrollment failed: {e}")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Run the agent daemon."""
    from valet_agent.main import main as run_daemon

    run_daemon()
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show agent status and configuration."""
    import subprocess
    import time

    import psutil

    from valet_agent.config import AgentConfig, get_default_paths

    print(f"🎩 DeviceValet Linux Agent v{__version__}")
    print()

    # Load config
    try:
        config = AgentConfig()
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return 1

    # Check config file (use dynamic path)
    config_file = get_default_paths()["env_file"]
    if config_file.exists():
        print(f"📁 Config file: {config_file} ✓")
    else:
        print(f"📁 Config file: {config_file} (not found)")

    print()
    print("Configuration:")
    print(f"  Server URL:    {config.server_url or '(not set)'}")
    print(f"  Device ID:     {config.device_id or '(not enrolled)'}")
    print(f"  Organization:  {config.organization_id or '(not enrolled)'}")
    print(
        f"  Auth Token:    {'****' + config.auth_token[-8:] if config.auth_token else '(not set)'}"
    )
    print()
    print("Settings:")
    print(f"  Check-in interval: {config.checkin_interval_seconds}s")
    print(f"  Report location:   {config.report_location}")
    print(f"  BeaconDB enabled:  {config.beacondb_enabled}")
    print(f"  MQTT enabled:      {config.mqtt_enabled}")
    if config.mqtt_enabled and config.mqtt_broker_url:
        print(f"  MQTT broker:       {config.mqtt_broker_url}")
    print()

    # Live System Stats
    print("System Stats:")

    # Uptime
    uptime_sec = int(time.time() - psutil.boot_time())
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    mins = (uptime_sec % 3600) // 60
    if days > 0:
        uptime_str = f"{days}d {hours}h {mins}m"
    elif hours > 0:
        uptime_str = f"{hours}h {mins}m"
    else:
        uptime_str = f"{mins}m"
    print(f"  Uptime:        {uptime_str}")

    # CPU
    cpu_pct = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    print(f"  CPU:           {cpu_pct}% ({cpu_count} cores)")

    # Memory
    mem = psutil.virtual_memory()
    mem_used_gb = (mem.total - mem.available) / (1024**3)
    mem_total_gb = mem.total / (1024**3)
    print(f"  Memory:        {mem_used_gb:.1f}/{mem_total_gb:.1f} GB ({mem.percent}%)")

    # Disk (root)
    disk = psutil.disk_usage("/")
    disk_used_gb = (disk.total - disk.free) / (1024**3)
    disk_total_gb = disk.total / (1024**3)
    print(f"  Disk (/):      {disk_used_gb:.0f}/{disk_total_gb:.0f} GB ({disk.percent}%)")

    # Temperatures (quick summary)
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            # Find the most relevant CPU temp
            cpu_temp = None
            for chip_name in ["k10temp", "coretemp", "cpu_thermal"]:
                if chip_name in temps:
                    readings = temps[chip_name]
                    for t in readings:
                        if t.current and t.current > 0:
                            cpu_temp = t.current
                            break
                    if cpu_temp:
                        break

            if cpu_temp:
                print(f"  CPU Temp:      {cpu_temp:.0f}°C")
    except (AttributeError, NotImplementedError):
        pass

    print()

    # Check if enrolled
    if not config.device_id:
        print("⚠️  Device not enrolled. Run: valet-agent enroll")
        print("   Or with activation URL: valet-agent enroll --url '<activation-url>'")
        return 1

    # Check systemd service
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "valet-agent"],
            capture_output=True,
            text=True,
        )
        service_status = result.stdout.strip()
        if service_status == "active":
            print("🟢 Service status: running")
        elif service_status == "inactive":
            print("⚪ Service status: stopped")
        else:
            print(f"🟡 Service status: {service_status}")
    except FileNotFoundError:
        print("ℹ️  systemd not available")

    return 0


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    print(f"valet-agent {__version__}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show detailed system hardware information."""
    import json

    from valet_agent.hardware import collect_detailed_hardware_info, hardware_info_to_dict

    info = collect_detailed_hardware_info()

    # JSON output mode
    if getattr(args, "json", False):
        data = hardware_info_to_dict(info)
        print(json.dumps(data, indent=2, default=str))
        return 0

    show_virtual = not getattr(args, "no_virtual", False)

    print(f"🎩 DeviceValet Linux Agent v{__version__}")
    print()
    print("Collecting hardware information...")
    print()

    # OS Info (at the top for quick identification)
    print("━" * 60)
    print("🐧 OPERATING SYSTEM")
    print("━" * 60)
    if info.os.pretty_name:
        print(f"  Distribution:  {info.os.pretty_name}")
    elif info.os.name:
        version_str = f" {info.os.version}" if info.os.version else ""
        print(f"  Distribution:  {info.os.name}{version_str}")
    if info.os.kernel_version:
        print(f"  Kernel:        {info.os.kernel_version} ({info.os.kernel_arch or 'unknown'})")
    if info.os.uptime_seconds:
        days = info.os.uptime_seconds // 86400
        hours = (info.os.uptime_seconds % 86400) // 3600
        mins = (info.os.uptime_seconds % 3600) // 60
        if days > 0:
            uptime_str = f"{days}d {hours}h {mins}m"
        elif hours > 0:
            uptime_str = f"{hours}h {mins}m"
        else:
            uptime_str = f"{mins}m"
        print(f"  Uptime:        {uptime_str}")
    print()

    # System
    print("━" * 60)
    print("📟 SYSTEM")
    print("━" * 60)
    print(f"  Manufacturer:  {info.system.manufacturer or 'Unknown'}")
    print(f"  Product:       {info.system.product_name or 'Unknown'}")
    if info.system.version:
        print(f"  Version:       {info.system.version}")
    if info.system.serial_number:
        print(f"  Serial:        {info.system.serial_number}")
    if info.system.uuid:
        print(f"  UUID:          {info.system.uuid}")
    print(f"  Chassis:       {info.chassis.chassis_type or 'Unknown'}")
    print()

    # BIOS
    print("━" * 60)
    print("💾 BIOS/UEFI")
    print("━" * 60)
    print(f"  Vendor:        {info.bios.vendor or 'Unknown'}")
    print(f"  Version:       {info.bios.version or 'Unknown'}")
    print(f"  Date:          {info.bios.release_date or 'Unknown'}")
    print()

    # Baseboard
    print("━" * 60)
    print("🔧 MOTHERBOARD")
    print("━" * 60)
    print(f"  Manufacturer:  {info.baseboard.manufacturer or 'Unknown'}")
    print(f"  Product:       {info.baseboard.product_name or 'Unknown'}")
    if info.baseboard.version:
        print(f"  Version:       {info.baseboard.version}")
    print()

    # CPU
    print("━" * 60)
    print("⚡ PROCESSOR")
    print("━" * 60)
    print(f"  Model:         {info.cpu.model_name or 'Unknown'}")
    print(f"  Architecture:  {info.cpu.architecture or 'Unknown'}")
    print(
        f"  Cores:         {info.cpu.physical_cores or '?'} physical, {info.cpu.logical_cores or '?'} logical"
    )
    if info.cpu.sockets and info.cpu.sockets > 1:
        print(f"  Sockets:       {info.cpu.sockets}")
    if info.cpu.current_frequency_mhz:
        freq_str = f"{info.cpu.current_frequency_mhz:.0f} MHz"
        if info.cpu.max_frequency_mhz:
            freq_str += f" (max: {info.cpu.max_frequency_mhz:.0f} MHz)"
        print(f"  Frequency:     {freq_str}")
    if info.cpu.cache_l3_kb:
        cache_parts = []
        if info.cpu.cache_l1d_kb:
            cache_parts.append(f"L1d: {info.cpu.cache_l1d_kb}KB")
        if info.cpu.cache_l2_kb:
            l2_mb = info.cpu.cache_l2_kb / 1024
            if l2_mb >= 1:
                cache_parts.append(f"L2: {l2_mb:.0f}MB")
            else:
                cache_parts.append(f"L2: {info.cpu.cache_l2_kb}KB")
        if info.cpu.cache_l3_kb:
            l3_mb = info.cpu.cache_l3_kb / 1024
            cache_parts.append(f"L3: {l3_mb:.0f}MB")
        print(f"  Cache:         {', '.join(cache_parts)}")
    if info.cpu.virtualization:
        virt_name = "Intel VT-x" if info.cpu.virtualization == "vmx" else "AMD-V"
        print(f"  Virtualization: {virt_name}")
    print()

    # Memory
    print("━" * 60)
    print("🧠 MEMORY")
    print("━" * 60)
    if info.memory.total_mb:
        total_gb = info.memory.total_mb / 1024
        avail_gb = (info.memory.available_mb or 0) / 1024
        print(f"  Total:         {total_gb:.1f} GB")
        print(
            f"  Available:     {avail_gb:.1f} GB ({100 - (info.memory.percent_used or 0):.0f}% free)"
        )

    if info.memory.slots_total:
        print(f"  Slots:         {info.memory.slots_used or 0}/{info.memory.slots_total}")
    if info.memory.max_capacity_gb:
        print(f"  Max Capacity:  {info.memory.max_capacity_gb} GB")

    if info.memory.modules:
        print("  DIMMs:")
        for mod in info.memory.modules:
            size_gb = (mod.size_mb or 0) / 1024
            parts = [f"{size_gb:.0f}GB"]
            if mod.memory_type:
                parts.append(mod.memory_type)
            if mod.speed_mhz:
                parts.append(f"@ {mod.speed_mhz}MHz")
            if mod.manufacturer and mod.manufacturer != "Unknown":
                parts.append(f"({mod.manufacturer})")
            print(f"    {mod.locator or 'DIMM'}: {' '.join(parts)}")
    print()

    # Storage
    print("━" * 60)
    print("💽 STORAGE")
    print("━" * 60)
    for dev in info.storage:
        type_str = dev.device_type or "Unknown"
        if dev.interface and dev.interface != dev.device_type:
            type_str += f" ({dev.interface})"
        print(f"  /dev/{dev.name}: {dev.size_gb:.1f} GB {type_str}")
        if dev.model:
            print(f"    Model:       {dev.model}")
        if dev.serial:
            print(f"    Serial:      {dev.serial}")
        if dev.smart_status:
            status_icon = "✓" if dev.smart_status == "PASSED" else "✗"
            status_str = f"{status_icon} {dev.smart_status}"
            if dev.temperature_c:
                status_str += f" ({dev.temperature_c}°C)"
            print(f"    SMART:       {status_str}")
        if dev.partitions:
            for part in dev.partitions:
                mount = part.get("mountpoint") or "not mounted"
                fstype = part.get("fstype") or "unknown"
                print(f"    └── {part['name']}: {part['size_gb']:.1f}GB {fstype} → {mount}")
    print()

    # Network
    print("━" * 60)
    print("🌐 NETWORK")
    print("━" * 60)
    for iface in info.network:
        if iface.interface_type == "loopback":
            continue
        if not show_virtual and iface.interface_type == "virtual":
            continue

        state_icon = "●" if iface.state == "up" else "○"
        state_color = "up" if iface.state == "up" else "down"
        type_str = iface.interface_type or "unknown"

        print(f"  {state_icon} {iface.name} ({type_str}, {state_color})")

        if iface.mac_address:
            print(f"      MAC:     {iface.mac_address}")
        for ip in iface.ipv4_addresses:
            print(f"      IPv4:    {ip}")
        for ip in iface.ipv6_addresses:
            print(f"      IPv6:    {ip}")
        if iface.speed_mbps and iface.speed_mbps > 0:
            speed_str = f"{iface.speed_mbps} Mbps"
            if iface.speed_mbps >= 1000:
                speed_str = f"{iface.speed_mbps / 1000:.0f} Gbps"
            print(f"      Speed:   {speed_str}")
        if iface.driver:
            print(f"      Driver:  {iface.driver}")
    print()

    # GPUs
    if info.gpus:
        print("━" * 60)
        print("🎮 GRAPHICS")
        print("━" * 60)
        for gpu in info.gpus:
            print(f"  {gpu.name}")
            if gpu.vendor:
                print(f"    Vendor:    {gpu.vendor}")
            if gpu.driver:
                print(f"    Driver:    {gpu.driver}")
            if gpu.pci_slot:
                print(f"    PCI:       {gpu.pci_slot}")
        print()

    # Battery
    if info.battery and info.battery.present:
        print("━" * 60)
        print("🔋 BATTERY")
        print("━" * 60)
        status_icon = "🔌" if info.battery.status == "Charging" else "🔋"
        print(f"  Status:        {status_icon} {info.battery.status} ({info.battery.percent:.0f}%)")
        if info.battery.time_remaining_minutes and info.battery.time_remaining_minutes > 0:
            hours = info.battery.time_remaining_minutes // 60
            mins = info.battery.time_remaining_minutes % 60
            print(f"  Time Left:     {hours}h {mins}m")
        if info.battery.health_percent:
            print(f"  Health:        {info.battery.health_percent:.0f}%")
        if info.battery.cycle_count:
            print(f"  Cycles:        {info.battery.cycle_count}")
        if info.battery.technology:
            print(f"  Technology:    {info.battery.technology}")
        print()

    # Thermal Sensors
    if info.thermals:
        print("━" * 60)
        print("🌡️  TEMPERATURES")
        print("━" * 60)
        for sensor in info.thermals:
            temp_str = f"{sensor.current_c}°C"
            if sensor.high_c:
                temp_str += f" (warn: {sensor.high_c}°C)"
            if sensor.critical_c:
                temp_str += f" (crit: {sensor.critical_c}°C)"

            # Color indicator based on temperature vs thresholds
            current = sensor.current_c or 0.0
            if sensor.critical_c and current >= sensor.critical_c:
                indicator = "🔴"  # Critical
            elif sensor.high_c and current >= sensor.high_c:
                indicator = "🟡"  # Warning
            else:
                indicator = "🟢"  # Normal

            print(f"  {indicator} {sensor.label}: {temp_str}")
        print()

    # Top Processes
    if info.top_processes:
        print("━" * 60)
        print("📊 TOP PROCESSES")
        print("━" * 60)
        # Header
        print(f"  {'PID':>7}  {'CPU%':>5}  {'MEM%':>5}  {'MEM':>8}  {'USER':<10}  NAME")
        print(f"  {'-' * 7}  {'-' * 5}  {'-' * 5}  {'-' * 8}  {'-' * 10}  {'-' * 20}")
        for proc in info.top_processes:
            mem_str = (
                f"{proc.memory_mb:.0f}MB"
                if proc.memory_mb < 1024
                else f"{proc.memory_mb / 1024:.1f}GB"
            )
            user = (proc.user or "?")[:10]
            name = proc.name[:30]
            print(
                f"  {proc.pid:>7}  {proc.cpu_percent:>5.1f}  {proc.memory_percent:>5.1f}  {mem_str:>8}  {user:<10}  {name}"
            )
        print()

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="valet-agent",
        description="DeviceValet Linux Agent - Fleet management daemon",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # enroll command
    enroll_parser = subparsers.add_parser(
        "enroll",
        help="Enroll this device with DeviceValet server",
    )
    enroll_parser.add_argument(
        "--url",
        "-u",
        help="Activation URL from dashboard (or set VALET_ACTIVATION_URL)",
    )
    enroll_parser.add_argument(
        "--token",
        "-t",
        help="Enrollment token (or set VALET_ENROLLMENT_TOKEN)",
    )
    enroll_parser.add_argument(
        "--server",
        "-s",
        help="Server URL (or set VALET_SERVER_URL)",
    )
    enroll_parser.add_argument(
        "--mqtt-url",
        help="MQTT broker URL (optional, derived from server if not set)",
    )
    enroll_parser.add_argument(
        "--config-dir",
        default=None,
        help="Configuration directory (auto-detected based on user)",
    )
    enroll_parser.set_defaults(func=cmd_enroll)

    # run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run the agent daemon (default if no command specified)",
    )
    run_parser.set_defaults(func=cmd_run)

    # status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show agent status and configuration",
    )
    status_parser.set_defaults(func=cmd_status)

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show detailed system hardware information",
    )
    info_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON for machine parsing",
    )
    info_parser.add_argument(
        "--no-virtual",
        action="store_true",
        help="Hide virtual network interfaces (veth, docker, etc.)",
    )
    info_parser.set_defaults(func=cmd_info)

    # Parse arguments
    args = parser.parse_args()

    # Handle --version
    if args.version:
        return cmd_version(args)

    # Default to 'run' if no command specified
    if not args.command:
        args.func = cmd_run

    # Execute command
    if hasattr(args, "func"):
        result: int = args.func(args)
        return result
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
