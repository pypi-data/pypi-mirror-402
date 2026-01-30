"""Pydantic models for the Uma API client."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class FanInfo(BaseModel):
    """Fan information from sensors."""

    name: str | None = Field(None, description="Fan name", examples=["CPU Fan"])
    rpm: int | None = Field(None, description="Fan speed in RPM", examples=[1200])

    model_config = {"frozen": True, "extra": "allow"}


class SystemInfo(BaseModel):
    """System information response from the Unraid server."""

    # Basic info
    hostname: str | None = Field(None, description="Server hostname")
    version: str | None = Field(None, description="Unraid version")
    agent_version: str | None = Field(None, description="Agent version")
    uptime_seconds: int | None = Field(None, description="System uptime in seconds")

    # CPU Information
    cpu_usage_percent: float | None = Field(None, description="CPU usage percentage")
    cpu_model: str | None = Field(None, description="CPU model name")
    cpu_cores: int | None = Field(None, description="Number of CPU cores")
    cpu_threads: int | None = Field(None, description="Number of CPU threads")
    cpu_mhz: float | None = Field(None, description="CPU frequency in MHz")
    cpu_per_core_usage: dict[str, float] | None = Field(None, description="Per-core CPU usage")
    cpu_temp_celsius: float | None = Field(None, description="CPU temperature in Celsius")

    # Memory Information
    ram_usage_percent: float | None = Field(None, description="RAM usage percentage")
    ram_total_bytes: int | None = Field(None, description="Total RAM in bytes")
    ram_used_bytes: int | None = Field(None, description="Used RAM in bytes")
    ram_free_bytes: int | None = Field(None, description="Free RAM in bytes")
    ram_buffers_bytes: int | None = Field(None, description="RAM buffers in bytes")
    ram_cached_bytes: int | None = Field(None, description="Cached RAM in bytes")

    # System Information
    server_model: str | None = Field(None, description="Server model")
    motherboard_model: str | None = Field(None, description="Motherboard model")
    bios_version: str | None = Field(None, description="BIOS version")
    bios_date: str | None = Field(None, description="BIOS date")

    # Additional System Information
    openssl_version: str | None = Field(None, description="OpenSSL version")
    kernel_version: str | None = Field(None, description="Kernel version")

    # Virtualization Features
    hvm_enabled: bool | None = Field(None, description="Hardware virtualization (HVM) enabled")
    iommu_enabled: bool | None = Field(None, description="IOMMU enabled")

    # Additional Metrics
    fans: list[FanInfo] | None = Field(None, description="Fan information")
    motherboard_temp_celsius: float | None = Field(
        None, description="Motherboard temperature in Celsius"
    )
    parity_check_speed: str | None = Field(None, description="Parity check speed")

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


ArrayState = Literal["STARTED", "STOPPED", "STARTING", "STOPPING", "Started", "Stopped"]


class ArrayStatus(BaseModel):
    """Array status response."""

    state: ArrayState | str | None = Field(None, description="Array state")

    # Disk counts (API uses num_disks, num_data_disks, num_parity_disks)
    num_disks: int | None = Field(None, description="Total number of disks")
    num_data_disks: int | None = Field(None, description="Number of data disks")
    num_parity_disks: int | None = Field(None, description="Number of parity disks")

    # Capacity (API uses total_bytes, not size_bytes)
    total_bytes: int | None = Field(None, description="Total array size in bytes")
    used_bytes: int | None = Field(None, description="Used space in bytes")
    free_bytes: int | None = Field(None, description="Free space in bytes")

    # Usage (API uses used_percent, not usage_percent)
    used_percent: float | None = Field(None, description="Array usage percentage")

    # Parity information
    parity_valid: bool | None = Field(None, description="Whether parity is valid")
    parity_check_status: str | None = Field(
        None, description="Parity check status (e.g., 'idle', 'running')"
    )
    parity_check_progress: float | None = Field(
        None, description="Parity check progress percentage"
    )

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


DiskRole = Literal["parity", "parity2", "data", "cache", "pool", "docker_vdisk", "log"]
SpinState = Literal["active", "standby", "idle", "unknown"]


class SMARTAttribute(BaseModel):
    """SMART attribute information."""

    id: int | None = Field(None, description="Attribute ID")
    name: str | None = Field(None, description="Attribute name")
    value: int | None = Field(None, description="Current value")
    worst: int | None = Field(None, description="Worst recorded value")
    threshold: int | None = Field(None, description="Threshold value")
    raw_value: str | None = Field(None, description="Raw value")
    when_failed: str | None = Field(None, description="When the attribute failed")

    model_config = {"frozen": True, "extra": "allow"}


class DiskInfo(BaseModel):
    """Disk information response."""

    # Disk identification
    id: str | None = Field(None, description="Disk identifier")
    device: str | None = Field(None, description="Device path")
    name: str | None = Field(None, description="Disk name")
    serial_number: str | None = Field(None, description="Disk serial number")
    model: str | None = Field(None, description="Disk model")
    role: str | None = Field(None, description="Disk role (parity, data, cache, pool)")

    # Capacity
    size_bytes: int | None = Field(None, description="Disk size in bytes")
    used_bytes: int | None = Field(None, description="Used space in bytes")
    free_bytes: int | None = Field(None, description="Free space in bytes")
    usage_percent: float | None = Field(None, description="Usage percentage")

    # Mount information
    mount_point: str | None = Field(None, description="Mount point")
    filesystem: str | None = Field(None, description="Filesystem type")

    # State and temperature
    temperature_celsius: float | None = Field(None, description="Disk temperature in Celsius")
    temp_warning: int | None = Field(
        None, description="Per-disk warning temperature threshold (null = use global default)"
    )
    temp_critical: int | None = Field(
        None, description="Per-disk critical temperature threshold (null = use global default)"
    )
    spin_state: str | None = Field(None, description="Disk spin state (active, standby, unknown)")
    spindown_delay: int | None = Field(None, description="Spindown delay in minutes")
    status: str | None = Field(None, description="Disk status")

    # SMART information
    smart_status: str | None = Field(None, description="SMART status (PASSED, FAILED)")
    smart_errors: int | None = Field(None, description="Number of SMART errors")
    smart_attributes: dict[str, SMARTAttribute] | None = Field(
        None, description="Enhanced SMART attributes"
    )

    # Power information
    power_on_hours: int | None = Field(None, description="Power on hours")
    power_cycle_count: int | None = Field(None, description="Power cycle count")

    # I/O Statistics
    read_bytes: int | None = Field(None, description="Total bytes read")
    write_bytes: int | None = Field(None, description="Total bytes written")
    read_ops: int | None = Field(None, description="Total read operations")
    write_ops: int | None = Field(None, description="Total write operations")
    io_utilization_percent: float | None = Field(None, description="I/O utilization percentage")

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


ContainerState = Literal["running", "stopped", "paused", "created", "exited", "dead"]


class PortMapping(BaseModel):
    """Docker container port mapping."""

    public_port: int | None = Field(None, description="Public (host) port")
    private_port: int | None = Field(None, description="Private (container) port")
    type: str | None = Field(None, description="Protocol type (tcp, udp)")

    model_config = {"frozen": True, "extra": "allow"}


class VolumeMapping(BaseModel):
    """Docker container volume mapping."""

    host_path: str | None = Field(None, description="Host path")
    container_path: str | None = Field(None, description="Container path")
    mode: str | None = Field(None, description="Mount mode (rw, ro)")

    model_config = {"frozen": True, "extra": "allow"}


class ContainerInfo(BaseModel):
    """Docker container information response."""

    # Identification
    id: str | None = Field(None, description="Container ID")
    name: str | None = Field(None, description="Container name")
    image: str | None = Field(None, description="Container image")
    version: str | None = Field(None, description="Container version")

    # State
    state: str | None = Field(None, description="Container state")
    status: str | None = Field(None, description="Container status string")
    uptime: str | None = Field(None, description="Container uptime")

    # Resource usage
    cpu_percent: float | None = Field(None, description="CPU usage percentage")
    memory_usage_bytes: int | None = Field(None, description="Memory usage in bytes")
    memory_limit_bytes: int | None = Field(None, description="Memory limit in bytes")
    memory_display: str | None = Field(None, description="Memory usage display (e.g., '1 GiB')")

    # Network
    network_mode: str | None = Field(None, description="Network mode (bridge, host, etc.)")
    ip_address: str | None = Field(None, description="Container IP address")
    network_rx_bytes: int | None = Field(None, description="Network bytes received")
    network_tx_bytes: int | None = Field(None, description="Network bytes transmitted")

    # Port and volume mappings
    ports: list[PortMapping] | None = Field(None, description="Port mappings")
    port_mappings: list[str] | None = Field(None, description="Port mappings as strings")
    volume_mappings: list[VolumeMapping] | None = Field(None, description="Volume mappings")

    # Configuration
    restart_policy: str | None = Field(None, description="Restart policy")

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


VMState = Literal["running", "stopped", "paused", "shut off", "crashed", "suspended"]


class VMInfo(BaseModel):
    """Virtual machine information response."""

    # Identification
    id: str | None = Field(None, description="VM ID")
    name: str | None = Field(None, description="VM name")
    state: str | None = Field(None, description="VM state")

    # CPU
    cpu_count: int | None = Field(None, description="Number of CPUs")
    guest_cpu_percent: float | None = Field(None, description="Guest CPU usage percentage")
    host_cpu_percent: float | None = Field(None, description="Host CPU usage percentage")

    # Memory (API uses memory_allocated_bytes and memory_used_bytes)
    memory_allocated_bytes: int | None = Field(None, description="Memory allocated in bytes")
    memory_used_bytes: int | None = Field(None, description="Memory used in bytes")
    memory_display: str | None = Field(None, description="Memory usage display")

    # Disk
    disk_path: str | None = Field(None, description="VM disk path")
    disk_size_bytes: int | None = Field(None, description="VM disk size in bytes")
    disk_read_bytes: int | None = Field(None, description="Disk bytes read")
    disk_write_bytes: int | None = Field(None, description="Disk bytes written")

    # Network
    network_rx_bytes: int | None = Field(None, description="Network bytes received")
    network_tx_bytes: int | None = Field(None, description="Network bytes transmitted")

    # Configuration
    autostart: bool | None = Field(None, description="VM autostart enabled")
    persistent: bool | None = Field(None, description="VM is persistent")

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ShareInfo(BaseModel):
    """User share information response."""

    name: str | None = Field(None, description="Share name")
    path: str | None = Field(None, description="Share path")

    # Capacity
    total_bytes: int | None = Field(None, description="Total size in bytes")
    used_bytes: int | None = Field(None, description="Used space in bytes")
    free_bytes: int | None = Field(None, description="Free space in bytes")
    usage_percent: float | None = Field(None, description="Usage percentage")

    # Configuration
    comment: str | None = Field(None, description="Share comment/description")
    security: str | None = Field(None, description="Security setting (public, private, secure)")
    use_cache: str | None = Field(None, description="Cache usage (yes, no, only, prefer)")
    storage: str | None = Field(
        None, description="Storage type (cache, array, cache+array, unknown)"
    )

    # Export settings
    smb_export: bool | None = Field(None, description="Is share exported via SMB?")
    nfs_export: bool | None = Field(None, description="Is share exported via NFS?")

    # Cache configuration
    cache_pool: str | None = Field(
        None, description="Primary cache pool name (empty/null = no cache)"
    )
    cache_pool2: str | None = Field(
        None, description="Secondary cache pool for 'prefer' destinations"
    )
    mover_action: str | None = Field(
        None,
        description="Computed mover action: no_cache, cache_only, cache_to_array, "
        "array_to_cache, cache_prefer",
    )

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class NetworkInterface(BaseModel):
    """Network interface information response."""

    # Basic info
    name: str | None = Field(None, description="Interface name")
    mac_address: str | None = Field(None, description="MAC address")
    ip_address: str | None = Field(None, description="IP address")
    netmask: str | None = Field(None, description="Network mask")
    broadcast: str | None = Field(None, description="Broadcast address")
    mtu: int | None = Field(None, description="MTU size")
    state: str | None = Field(None, description="Interface state")
    speed_mbps: int | None = Field(None, description="Link speed in Mbps")

    # Traffic stats - API uses bytes_received/bytes_sent, packets_received/packets_sent
    bytes_received: int | None = Field(None, description="Bytes received")
    bytes_sent: int | None = Field(None, description="Bytes transmitted")
    packets_received: int | None = Field(None, description="Packets received")
    packets_sent: int | None = Field(None, description="Packets transmitted")
    errors_received: int | None = Field(None, description="Receive errors")
    errors_sent: int | None = Field(None, description="Transmit errors")

    # Ethtool information
    duplex: str | None = Field(None, description="Duplex mode (Full, Half)")
    auto_negotiation: str | None = Field(None, description="Auto-negotiation status")
    link_detected: bool | None = Field(None, description="Link detected")
    port: str | None = Field(None, description="Port type")
    transceiver: str | None = Field(None, description="Transceiver type")
    mdix: str | None = Field(None, description="MDI-X status")
    phyad: int | None = Field(None, description="PHY address")
    message_level: str | None = Field(None, description="Message level")
    wake_on: str | None = Field(None, description="Wake-on-LAN status")

    # Supported capabilities
    supported_ports: list[str] | None = Field(None, description="Supported ports")
    supported_link_modes: list[str] | None = Field(None, description="Supported link modes")
    supported_pause_frame: str | None = Field(None, description="Supported pause frame")
    supported_fec_modes: list[str] | None = Field(None, description="Supported FEC modes")
    supports_auto_negotiation: bool | None = Field(None, description="Supports auto-negotiation")
    supports_wake_on: list[str] | None = Field(None, description="Supported wake-on modes")

    # Advertised capabilities
    advertised_link_modes: list[str] | None = Field(None, description="Advertised link modes")
    advertised_pause_frame: str | None = Field(None, description="Advertised pause frame")
    advertised_auto_negotiation: bool | None = Field(
        None, description="Advertised auto-negotiation"
    )
    advertised_fec_modes: list[str] | None = Field(None, description="Advertised FEC modes")

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class HardwareInfo(BaseModel):
    """Hardware information response (extracted from system info)."""

    cpu_model: str | None = Field(None, description="CPU model name")
    cpu_cores: int | None = Field(None, description="Number of CPU cores")
    cpu_threads: int | None = Field(None, description="Number of CPU threads")
    motherboard_model: str | None = Field(None, description="Motherboard model")
    bios_version: str | None = Field(None, description="BIOS version")
    bios_date: str | None = Field(None, description="BIOS date")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class GPUInfo(BaseModel):
    """GPU information response."""

    available: bool | None = Field(None, description="Whether GPU is available")
    index: int | None = Field(None, description="GPU index")
    pci_id: str | None = Field(None, description="PCI device ID")
    name: str | None = Field(None, description="GPU name")
    vendor: str | None = Field(None, description="GPU vendor")
    driver_version: str | None = Field(None, description="GPU driver version")
    utilization_gpu_percent: float | None = Field(None, description="GPU utilization percentage")
    utilization_memory_percent: float | None = Field(
        None, description="Memory utilization percentage"
    )
    memory_total_bytes: int | None = Field(None, description="Total GPU memory in bytes")
    memory_used_bytes: int | None = Field(None, description="Used GPU memory in bytes")
    temperature_celsius: float | None = Field(None, description="GPU temperature in Celsius")
    cpu_temperature_celsius: float | None = Field(None, description="CPU temperature in Celsius")
    power_draw_watts: float | None = Field(None, description="Power draw in watts")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class UPSInfo(BaseModel):
    """UPS information response (from apcupsd)."""

    # Basic info
    model: str | None = Field(None, description="UPS model")
    status: str | None = Field(None, description="UPS status (e.g., OL, OB)")

    # Battery info
    battery_charge_percent: float | None = Field(None, description="Battery charge percentage")
    load_percent: float | None = Field(None, description="Load percentage")

    # Runtime - API uses runtime_left_seconds
    runtime_left_seconds: int | None = Field(None, description="Battery runtime remaining in secs")

    # Power - API uses power_watts and nominal_power_watts
    power_watts: float | None = Field(None, description="Current power draw in watts")
    nominal_power_watts: float | None = Field(None, description="Nominal power in watts")

    # Connection status
    connected: bool | None = Field(None, description="Whether UPS is connected")

    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class HealthStatus(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")

    model_config = {"frozen": True, "extra": "allow"}


class ActionResponse(BaseModel):
    """Response from action endpoints (start, stop, etc.)."""

    success: bool = Field(..., description="Whether the action succeeded")
    message: str | None = Field(None, description="Response message")
    timestamp: str | None = Field(None, description="Action timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class APIError(BaseModel):
    """API error response."""

    success: bool = Field(False, description="Always false for errors")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: str | None = Field(None, description="Error timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class RegistrationInfo(BaseModel):
    """Unraid registration/license information."""

    type: str | None = Field(None, description="License type")
    state: str | None = Field(None, description="Registration state")
    key_file: str | None = Field(None, description="Key file path")
    guid: str | None = Field(None, description="Server GUID")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class LogFile(BaseModel):
    """Log file information."""

    name: str | None = Field(None, description="Log filename")
    path: str | None = Field(None, description="Log file path")
    size_bytes: int | None = Field(None, description="File size in bytes")
    modified_at: str | None = Field(None, description="Last modified timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class LogList(BaseModel):
    """List of available log files."""

    logs: list[LogFile] | None = Field(None, description="Available log files")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class LogContent(BaseModel):
    """Log file content response."""

    path: str | None = Field(None, description="Log file path")
    content: str | None = Field(None, description="Raw log content")
    lines: list[str] | None = Field(None, description="Log content as lines")
    total_lines: int | None = Field(None, description="Total lines in file")
    lines_returned: int | None = Field(None, description="Number of lines returned")
    start_line: int | None = Field(None, description="Start line number")
    end_line: int | None = Field(None, description="End line number")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class Notification(BaseModel):
    """Notification information."""

    id: str | None = Field(None, description="Notification ID")
    subject: str | None = Field(None, description="Notification subject")
    description: str | None = Field(None, description="Notification description")
    importance: str | None = Field(None, description="Importance level")
    timestamp: str | None = Field(None, description="Notification timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class NotificationCounts(BaseModel):
    """Notification counts by type."""

    info: int | None = Field(None, description="Info notifications")
    warning: int | None = Field(None, description="Warning notifications")
    alert: int | None = Field(None, description="Alert notifications")
    total: int | None = Field(None, description="Total notifications")

    model_config = {"frozen": True, "extra": "allow"}


class NotificationOverview(BaseModel):
    """Notification overview/summary."""

    unread: NotificationCounts | None = Field(None, description="Unread counts")
    archive: NotificationCounts | None = Field(None, description="Archive counts")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class NotificationsResponse(BaseModel):
    """Full notifications response."""

    overview: NotificationOverview | None = Field(None, description="Overview")
    notifications: list[Notification] | None = Field(None, description="Notification list")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class UnassignedDevice(BaseModel):
    """Unassigned device information."""

    device: str | None = Field(None, description="Device path")
    name: str | None = Field(None, description="Device name")
    size_bytes: int | None = Field(None, description="Device size in bytes")
    mounted: bool | None = Field(None, description="Whether mounted")
    filesystem: str | None = Field(None, description="Filesystem type")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class RemoteShare(BaseModel):
    """Remote share information."""

    name: str | None = Field(None, description="Share name")
    protocol: str | None = Field(None, description="Protocol (SMB, NFS)")
    server: str | None = Field(None, description="Remote server")
    mounted: bool | None = Field(None, description="Whether mounted")
    mount_point: str | None = Field(None, description="Mount point path")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class UnassignedDevicesResponse(BaseModel):
    """Unassigned devices response."""

    devices: list[UnassignedDevice] | None = Field(None, description="Unassigned devices")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class RemoteSharesResponse(BaseModel):
    """Remote shares response."""

    remote_shares: list[RemoteShare] | None = Field(None, description="Remote shares")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class UnassignedInfo(BaseModel):
    """Full unassigned devices and remote shares response."""

    devices: list[UnassignedDevice] | None = Field(None, description="Unassigned devices")
    remote_shares: list[RemoteShare] | None = Field(None, description="Remote shares")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class HardwareFullInfo(BaseModel):
    """Full hardware information from /hardware/full."""

    bios: dict[str, Any] | None = Field(None, description="BIOS information")
    system: dict[str, Any] | None = Field(None, description="System information")
    baseboard: dict[str, Any] | None = Field(None, description="Baseboard information")
    chassis: dict[str, Any] | None = Field(None, description="Chassis information")
    processor: dict[str, Any] | None = Field(None, description="Processor information")
    memory: dict[str, Any] | None = Field(None, description="Memory information")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class BIOSInfo(BaseModel):
    """BIOS information from DMI data."""

    vendor: str | None = Field(None, description="BIOS vendor")
    version: str | None = Field(None, description="BIOS version")
    release_date: str | None = Field(None, description="BIOS release date")
    revision: str | None = Field(None, description="BIOS revision")
    rom_size: str | None = Field(None, description="BIOS ROM size")
    runtime_size: str | None = Field(None, description="BIOS runtime size")
    address: str | None = Field(None, description="BIOS address")
    characteristics: list[str] | None = Field(None, description="BIOS characteristics")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class BaseboardInfo(BaseModel):
    """Motherboard/baseboard information from DMI data."""

    manufacturer: str | None = Field(None, description="Board manufacturer")
    product_name: str | None = Field(None, description="Board product name")
    serial_number: str | None = Field(None, description="Board serial number")
    asset_tag: str | None = Field(None, description="Asset tag")
    location_in_chassis: str | None = Field(None, description="Location in chassis")
    features: list[str] | None = Field(None, description="Board features")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class CPUHardwareInfo(BaseModel):
    """CPU hardware information from DMI data."""

    socket_designation: str | None = Field(None, description="CPU socket")
    processor_type: str | None = Field(None, description="Processor type")
    processor_family: str | None = Field(None, description="Processor family")
    processor_manufacturer: str | None = Field(None, description="Processor manufacturer")
    processor_version: str | None = Field(None, description="Processor version")
    max_speed: str | None = Field(None, description="Maximum CPU speed")
    current_speed: str | None = Field(None, description="Current CPU speed")
    core_count: int | None = Field(None, description="Number of cores")
    thread_count: int | None = Field(None, description="Number of threads")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class MemoryArrayInfo(BaseModel):
    """Physical memory array information from DMI data."""

    location: str | None = Field(None, description="Memory location")
    use: str | None = Field(None, description="Memory use")
    error_correction_type: str | None = Field(None, description="Error correction type")
    maximum_capacity: str | None = Field(None, description="Maximum memory capacity")
    number_of_devices: int | None = Field(None, description="Number of memory devices")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class MemoryDeviceInfo(BaseModel):
    """Individual memory device (DIMM) information from DMI data."""

    locator: str | None = Field(None, description="DIMM locator")
    bank_locator: str | None = Field(None, description="Bank locator")
    type: str | None = Field(None, description="Memory type")
    size: str | None = Field(None, description="Memory size")
    speed: str | None = Field(None, description="Memory speed")
    manufacturer: str | None = Field(None, description="Memory manufacturer")
    serial_number: str | None = Field(None, description="Memory serial number")
    part_number: str | None = Field(None, description="Memory part number")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class CPUCacheInfo(BaseModel):
    """CPU cache information from DMI data."""

    socket_designation: str | None = Field(None, description="Cache designation")
    configuration: str | None = Field(None, description="Cache configuration")
    operational_mode: str | None = Field(None, description="Operational mode")
    location: str | None = Field(None, description="Cache location")
    installed_size: str | None = Field(None, description="Installed cache size")
    maximum_size: str | None = Field(None, description="Maximum cache size")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class AccessUrl(BaseModel):
    """Network access URL."""

    type: str | None = Field(None, description="URL type (lan, wan, mdns, ipv6)")
    name: str | None = Field(None, description="URL name")
    ipv4: str | None = Field(None, description="IPv4 URL")
    ipv6: str | None = Field(None, description="IPv6 URL")

    model_config = {"frozen": True, "extra": "allow"}


class NetworkAccessUrls(BaseModel):
    """Network access URLs."""

    urls: list[AccessUrl] | None = Field(None, description="Access URLs")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class SystemSettings(BaseModel):
    """System settings."""

    server_name: str | None = Field(None, description="Server name")
    timezone: str | None = Field(None, description="Timezone")
    use_ssl: bool | None = Field(None, description="SSL enabled")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class DockerSettings(BaseModel):
    """Docker settings."""

    enabled: bool | None = Field(None, description="Docker enabled")
    image_path: str | None = Field(None, description="Docker image path")
    auto_start: bool | None = Field(None, description="Auto start enabled")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class VMSettings(BaseModel):
    """VM settings."""

    enabled: bool | None = Field(None, description="VMs enabled")
    default_path: str | None = Field(None, description="Default VM path")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class DiskSettings(BaseModel):
    """Disk settings from /settings/disk-thresholds endpoint."""

    spindown_delay_minutes: int | None = Field(None, description="Spindown delay in minutes")
    start_array: bool | None = Field(None, description="Auto-start array on boot")
    spinup_groups: bool | None = Field(None, description="Enable spinup groups")
    shutdown_timeout_seconds: int | None = Field(None, description="Shutdown timeout in seconds")
    default_filesystem: str | None = Field(None, description="Default filesystem")
    hdd_temp_warning_celsius: int | None = Field(
        None, description="HDD warning temperature threshold in Celsius"
    )
    hdd_temp_critical_celsius: int | None = Field(
        None, description="HDD critical temperature threshold in Celsius"
    )
    ssd_temp_warning_celsius: int | None = Field(
        None, description="SSD warning temperature threshold in Celsius"
    )
    ssd_temp_critical_celsius: int | None = Field(
        None, description="SSD critical temperature threshold in Celsius"
    )
    warning_utilization_percent: int | None = Field(
        None, description="Warning disk utilization percentage"
    )
    critical_utilization_percent: int | None = Field(
        None, description="Critical disk utilization percentage"
    )
    nvme_power_monitoring: bool | None = Field(None, description="Enable NVMe power monitoring")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ShareConfig(BaseModel):
    """User share configuration."""

    name: str | None = Field(None, description="Share name")
    comment: str | None = Field(None, description="Share comment/description")
    allocator: str | None = Field(None, description="Disk allocation method")
    floor: str | None = Field(None, description="Minimum free space floor")
    split_level: str | None = Field(None, description="Split level setting")
    include_disks: list[str] | None = Field(None, description="Included disks")
    exclude_disks: list[str] | None = Field(None, description="Excluded disks")
    use_cache: str | None = Field(None, description="Cache usage setting")
    export: str | None = Field(None, description="Export setting")
    security: str | None = Field(None, description="Security setting")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class NetworkConfig(BaseModel):
    """Network interface configuration."""

    interface: str | None = Field(None, description="Interface name")
    description: str | None = Field(None, description="Interface description")
    protocol: str | None = Field(None, description="Protocol (ipv4, ipv6)")
    use_dhcp: bool | None = Field(None, description="Whether DHCP is enabled")
    ip_address: str | None = Field(None, description="Static IP address")
    netmask: str | None = Field(None, description="Network mask")
    gateway: str | None = Field(None, description="Default gateway")
    dns_server: str | None = Field(None, description="DNS server")
    mtu: int | None = Field(None, description="MTU size")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class UserScript(BaseModel):
    """User script information."""

    name: str | None = Field(None, description="Script name")
    description: str | None = Field(None, description="Script description")
    script_path: str | None = Field(None, description="Script path")
    schedule: str | None = Field(None, description="Schedule")
    running: bool | None = Field(None, description="Currently running")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class UserScriptExecuteResponse(BaseModel):
    """User script execution response."""

    success: bool = Field(..., description="Whether execution succeeded")
    message: str | None = Field(None, description="Response message")
    output: str | None = Field(None, description="Script output")
    exit_code: int | None = Field(None, description="Script exit code")
    timestamp: str | None = Field(None, description="Execution timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ParityCheckRecord(BaseModel):
    """Parity check history record."""

    action: str | None = Field(None, description="Action type (e.g., 'Parity-Check')")
    date: str | None = Field(None, description="Check date (ISO 8601 format)")
    duration_seconds: int | None = Field(None, description="Duration in seconds")
    speed_mbps: float | None = Field(None, description="Check speed in MB/s")
    status: str | None = Field(None, description="Check status (e.g., 'OK' or error message)")
    errors: int | None = Field(None, description="Errors found")
    size_bytes: int | None = Field(None, description="Size checked in bytes")

    model_config = {"frozen": True, "extra": "allow"}


class ParityHistory(BaseModel):
    """Parity check history."""

    records: list[ParityCheckRecord] | None = Field(None, description="History records")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ParityStatus(BaseModel):
    """Parity check status response."""

    running: bool | None = Field(None, description="Whether parity check is running")
    paused: bool | None = Field(None, description="Whether parity check is paused")
    progress_percent: float | None = Field(None, description="Progress percentage")
    errors: int | None = Field(None, description="Errors found so far")
    speed_mb_per_sec: float | None = Field(None, description="Speed in MB/s")
    eta_seconds: int | None = Field(None, description="Estimated time remaining in seconds")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ZFSPool(BaseModel):
    """ZFS pool information."""

    name: str | None = Field(None, description="Pool name")
    state: str | None = Field(None, description="Pool state")
    size_bytes: int | None = Field(None, description="Pool size in bytes")
    used_bytes: int | None = Field(None, description="Used space in bytes")
    free_bytes: int | None = Field(None, description="Free space in bytes")
    health: str | None = Field(None, description="Pool health")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ZFSDataset(BaseModel):
    """ZFS dataset information."""

    name: str | None = Field(None, description="Dataset name")
    pool: str | None = Field(None, description="Parent pool")
    used_bytes: int | None = Field(None, description="Used space in bytes")
    available_bytes: int | None = Field(None, description="Available space in bytes")
    mountpoint: str | None = Field(None, description="Mount point")
    compression: str | None = Field(None, description="Compression type")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ZFSSnapshot(BaseModel):
    """ZFS snapshot information."""

    name: str | None = Field(None, description="Snapshot name")
    dataset: str | None = Field(None, description="Parent dataset")
    creation: str | None = Field(None, description="Creation timestamp")
    used_bytes: int | None = Field(None, description="Used space in bytes")
    referenced_bytes: int | None = Field(None, description="Referenced space in bytes")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class ZFSArcStats(BaseModel):
    """ZFS ARC statistics."""

    hit_ratio_percent: float | None = Field(None, description="ARC hit ratio percentage")
    size_bytes: int | None = Field(None, description="ARC size in bytes")
    target_size_bytes: int | None = Field(None, description="ARC target size in bytes")
    hits: int | None = Field(None, description="ARC hits")
    misses: int | None = Field(None, description="ARC misses")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class NUTInfo(BaseModel):
    """NUT (Network UPS Tools) information."""

    installed: bool | None = Field(None, description="NUT installed")
    running: bool | None = Field(None, description="NUT service running")
    config_mode: str | None = Field(None, description="Configuration mode")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class CollectorDetails(BaseModel):
    """Individual collector details from API."""

    name: str | None = Field(None, description="Collector name")
    enabled: bool | None = Field(None, description="Whether collector is enabled")
    interval_seconds: int | None = Field(
        None, description="Collection interval in seconds (0 if disabled)"
    )
    last_run: str | None = Field(None, description="Last collection timestamp")
    status: str | None = Field(
        None, description="Collector status (running, stopped, disabled, registered)"
    )
    required: bool | None = Field(None, description="True if collector cannot be disabled")
    error_count: int | None = Field(None, description="Error count")

    model_config = {"frozen": True, "extra": "allow"}


class CollectorInfo(BaseModel):
    """Individual collector response (nested structure from API).

    The API returns: {"success": bool, "message": str, "collector": {...}, "timestamp": str}
    """

    success: bool | None = Field(None, description="Whether the request succeeded")
    message: str | None = Field(None, description="Response message")
    collector: CollectorDetails | None = Field(None, description="Collector details")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


class CollectorStatus(BaseModel):
    """Collector status information (list of all collectors)."""

    total: int | None = Field(None, description="Total collectors")
    enabled_count: int | None = Field(None, description="Enabled collectors")
    disabled_count: int | None = Field(None, description="Disabled collectors")
    collectors: list[CollectorDetails] | None = Field(None, description="Collector details")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


# Issue #27: Parity schedule support
class ParitySchedule(BaseModel):
    """Parity check schedule configuration from /array/parity-check/schedule endpoint."""

    mode: str | None = Field(
        None, description="Schedule mode: disabled, daily, weekly, monthly, yearly"
    )
    day: int | None = Field(None, description="Day of week (0-6) for weekly mode")
    hour: int | None = Field(None, description="Hour to run")
    day_of_month: int | None = Field(None, description="Day of month for monthly mode")
    frequency: int | None = Field(None, description="Frequency multiplier")
    duration_hours: int | None = Field(None, description="Maximum duration in hours")
    cumulative: bool | None = Field(None, description="Enable cumulative/incremental parity")
    correcting: bool | None = Field(None, description="Auto-correct errors during check")
    pause_hour: int | None = Field(None, description="Hour to pause check (0-23)")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


# Issue #28: Mover settings support
class MoverSettings(BaseModel):
    """Mover settings from /settings/mover endpoint."""

    active: bool | None = Field(None, description="Is mover currently running")
    schedule: str | None = Field(None, description="Cron expression for mover schedule")
    logging: bool | None = Field(None, description="Enable mover logging")
    cache_floor_kb: int | None = Field(
        None, description="Minimum free space to leave on cache (KB)"
    )
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


# Issue #29: Docker/VM service status
class ServiceStatus(BaseModel):
    """Docker and VM service status from /settings/services endpoint."""

    docker_enabled: bool | None = Field(None, description="Docker service enabled")
    docker_autostart: bool | None = Field(None, description="Docker autostart enabled")
    vm_manager_enabled: bool | None = Field(None, description="VM manager enabled")
    vm_autostart: bool | None = Field(None, description="VM autostart enabled")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


# Issue #30: Update status
class UpdateStatus(BaseModel):
    """Update availability status from /updates endpoint."""

    current_version: str | None = Field(None, description="Current Unraid version")
    os_update_available: bool | None = Field(None, description="OS update available")
    total_plugins: int | None = Field(None, description="Total installed plugins")
    plugin_updates_count: int | None = Field(None, description="Number of plugins with updates")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


# Issue #31: Flash drive info
class FlashDriveInfo(BaseModel):
    """USB flash boot drive information from /system/flash endpoint."""

    device: str | None = Field(None, description="Device path (e.g., /dev/sda)")
    model: str | None = Field(None, description="Flash drive model")
    vendor: str | None = Field(None, description="Flash drive vendor")
    guid: str | None = Field(None, description="Server GUID from flash drive")
    size_bytes: int | None = Field(None, description="Flash drive size in bytes")
    used_bytes: int | None = Field(None, description="Used space in bytes")
    free_bytes: int | None = Field(None, description="Free space in bytes")
    usage_percent: float | None = Field(None, description="Usage percentage")
    smart_available: bool | None = Field(None, description="SMART data available")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


# Issue #32: Plugin list
class PluginInfo(BaseModel):
    """Individual plugin information."""

    name: str | None = Field(None, description="Plugin name")
    version: str | None = Field(None, description="Installed version")
    update_available: bool | None = Field(None, description="Update available for this plugin")

    model_config = {"frozen": True, "extra": "allow"}


class PluginList(BaseModel):
    """Plugin list from /plugins endpoint."""

    plugins: list[PluginInfo] | None = Field(None, description="List of installed plugins")
    total_plugins: int | None = Field(None, description="Total number of plugins")
    plugins_with_updates: int | None = Field(None, description="Plugins with available updates")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}


# Issue #34: Network services status
class NetworkServiceInfo(BaseModel):
    """Individual network service information."""

    name: str | None = Field(None, description="Service display name")
    enabled: bool | None = Field(None, description="Service is enabled")
    running: bool | None = Field(None, description="Service is currently running")
    port: int | None = Field(None, description="Service port number")
    description: str | None = Field(None, description="Service description")

    model_config = {"frozen": True, "extra": "allow"}


class NetworkServicesStatus(BaseModel):
    """Network services status from /settings/network-services endpoint."""

    smb: NetworkServiceInfo | None = Field(None, description="SMB (Windows file sharing)")
    nfs: NetworkServiceInfo | None = Field(None, description="NFS (Network File System)")
    afp: NetworkServiceInfo | None = Field(None, description="AFP (Apple Filing Protocol)")
    ftp: NetworkServiceInfo | None = Field(None, description="FTP (File Transfer Protocol)")
    ssh: NetworkServiceInfo | None = Field(None, description="SSH (Secure Shell)")
    telnet: NetworkServiceInfo | None = Field(None, description="Telnet (insecure)")
    avahi: NetworkServiceInfo | None = Field(None, description="Avahi (mDNS/DNS-SD)")
    netbios: NetworkServiceInfo | None = Field(None, description="NetBIOS name service")
    wsd: NetworkServiceInfo | None = Field(None, description="WSD (Web Services Discovery)")
    wireguard: NetworkServiceInfo | None = Field(None, description="WireGuard VPN")
    upnp: NetworkServiceInfo | None = Field(None, description="UPnP (Universal Plug and Play)")
    ntp: NetworkServiceInfo | None = Field(None, description="NTP server")
    syslog: NetworkServiceInfo | None = Field(None, description="Remote syslog server")
    services_enabled: int | None = Field(None, description="Number of enabled services")
    services_running: int | None = Field(None, description="Number of running services")
    timestamp: str | None = Field(None, description="Data collection timestamp")

    model_config = {"frozen": True, "extra": "allow"}
