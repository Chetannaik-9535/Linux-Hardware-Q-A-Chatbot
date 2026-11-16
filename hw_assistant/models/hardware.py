"""Pydantic models for structured hardware specifications."""

from __future__ import annotations

from pydantic import BaseModel, Field, computed_field


class CPUInfo(BaseModel):
    """Normalized CPU hardware details."""

    vendor: str = Field(..., description="CPU manufacturer/vendor (e.g. Intel, AMD, ARM)")
    model: str = Field(..., description="Full CPU model designation")
    architecture: str = Field(..., description="Instruction set architecture (e.g. x86_64, aarch64)")
    cores: int = Field(..., description="Number of physical CPU cores")
    threads: int = Field(..., description="Number of logical execution threads")
    max_frequency_mhz: float | None = Field(None, description="Maximum CPU clock frequency in MHz")
    min_frequency_mhz: float | None = Field(None, description="Minimum CPU clock frequency in MHz")
    current_frequency_mhz: float | None = Field(None, description="Current CPU clock frequency in MHz")
    l1d_cache: str | None = Field(None, description="L1 data cache size")
    l1i_cache: str | None = Field(None, description="L1 instruction cache size")
    l2_cache: str | None = Field(None, description="L2 cache size")
    l3_cache: str | None = Field(None, description="L3 cache size")
    flags: list[str] = Field(default_factory=list, description="Instruction set flags/features")
    raw_source: str = Field(default="lscpu", description="System utility or interface used")


class MemoryInfo(BaseModel):
    """Normalized volatile memory (RAM) usage details."""

    total_bytes: int = Field(..., description="Total system RAM in bytes")
    used_bytes: int = Field(..., description="RAM currently used in bytes")
    available_bytes: int = Field(..., description="RAM available for new applications in bytes")
    free_bytes: int = Field(..., description="Completely unallocated RAM in bytes")
    cached_bytes: int | None = Field(None, description="Memory used for disk caching/buffers")
    swap_total_bytes: int = Field(default=0, description="Total swap space in bytes")
    swap_used_bytes: int = Field(default=0, description="Used swap space in bytes")
    swap_free_bytes: int = Field(default=0, description="Available swap space in bytes")
    raw_source: str = Field(default="free", description="System utility or interface used")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_gb(self) -> float:
        """Total RAM in gigabytes (GiB base-2 rounded to 2 decimals)."""
        return round(self.total_bytes / (1024**3), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def used_gb(self) -> float:
        """Used RAM in gigabytes."""
        return round(self.used_bytes / (1024**3), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def available_gb(self) -> float:
        """Available RAM in gigabytes."""
        return round(self.available_bytes / (1024**3), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def utilization_percent(self) -> float:
        """Percentage of RAM currently in use."""
        if self.total_bytes <= 0:
            return 0.0
        return round((self.used_bytes / self.total_bytes) * 100.0, 1)


class MemoryModule(BaseModel):
    """Details of a single physical memory slot / module."""

    locator: str = Field(..., description="Slot locator ID (e.g., 'DIMM 0', 'Controller0-ChannelA')")
    installed: bool = Field(..., description="True if a memory module is inserted; False if empty")
    size_raw: str = Field(..., description="Raw capacity string (e.g. '16 GB', 'No Module Installed')")
    size_gb: float | None = Field(None, description="Capacity in GB if installed")
    memory_type: str | None = Field(None, description="Memory standard (e.g. DDR4, DDR5, LPDDR5)")
    speed_mhz: int | None = Field(None, description="Configured memory clock speed in MT/s or MHz")
    manufacturer: str | None = Field(None, description="Module manufacturer (e.g. Samsung, Crucial)")
    part_number: str | None = Field(None, description="OEM module part number")
    form_factor: str | None = Field(None, description="Module form factor (e.g. SODIMM, DIMM, Row of chips)")


class MemoryTopology(BaseModel):
    """Physical RAM topology, slots, and upgradeability."""

    total_slots: int | None = Field(None, description="Total physical motherboard memory slots")
    used_slots: int | None = Field(None, description="Number of slots populated with RAM")
    empty_slots: int | None = Field(None, description="Number of empty slots available for upgrade")
    modules: list[MemoryModule] = Field(default_factory=list, description="List of individual slot details")
    max_capacity_gb: float | None = Field(
        None,
        description="Maximum supported RAM capacity in GB reported by BIOS/DMI. None if unavailable."
    )
    is_upgradeable: bool | None = Field(
        None,
        description="Whether RAM can be upgraded (empty slots exist, or socketed modules can be replaced)"
    )
    is_soldered: bool | None = Field(
        None,
        description="Whether memory is soldered directly to motherboard (e.g. LPDDR/Row of chips)"
    )
    upgrade_assessment: str = Field(
        ...,
        description="Human-readable factual summary of upgrade potential based on slots and max capacity"
    )
    permission_denied: bool = Field(
        default=False,
        description="True if dmidecode failed due to missing root/sudo privileges"
    )
    notes: list[str] = Field(default_factory=list, description="Caveats, warnings, or missing permission details")


class BlockDevice(BaseModel):
    """Normalized block storage device (disk or partition)."""

    name: str = Field(..., description="Device name (e.g., nvme0n1, sda, sda1)")
    size: str = Field(..., description="Human-readable size (e.g. 512G, 1.8T)")
    type: str = Field(..., description="Device type: disk, part, rom, lvm, loop")
    mountpoint: str | None = Field(None, description="Filesystem mount path (e.g., '/', '/home')")
    model: str | None = Field(None, description="Device model string")
    rota: bool | None = Field(None, description="Rotational device flag (False = SSD, True = HDD)")
    is_ssd: bool | None = Field(None, description="True if SSD, False if HDD, None if indeterminate")
    transport: str | None = Field(None, description="Bus transport protocol: nvme, sata, usb, scsi, pcie")
    fstype: str | None = Field(None, description="Filesystem type (e.g. ext4, btrfs, vfat, ntfs)")
    children: list[BlockDevice] = Field(default_factory=list, description="Partitions or child devices")


class StorageInfo(BaseModel):
    """Storage devices collection with summary counts."""

    devices: list[BlockDevice] = Field(default_factory=list, description="Top-level storage disks")
    total_disks: int = Field(default=0, description="Total physical disk devices")
    ssd_count: int = Field(default=0, description="Number of detected solid-state drives (SSD)")
    hdd_count: int = Field(default=0, description="Number of detected rotational hard drives (HDD)")
    nvme_count: int = Field(default=0, description="Number of NVMe connected drives")
    sata_count: int = Field(default=0, description="Number of SATA connected drives")
    raw_source: str = Field(default="lsblk", description="System utility used")


class GPUInfo(BaseModel):
    """Normalized graphics processing unit (GPU) details."""

    vendor: str = Field(..., description="GPU vendor (e.g. NVIDIA, Intel, AMD)")
    model: str = Field(..., description="GPU model designation")
    driver_version: str | None = Field(None, description="Installed kernel/proprietary driver version")
    vram_mb: int | None = Field(None, description="Dedicated video memory in MB")
    pcie_slot: str | None = Field(None, description="PCI bus address (e.g. 0000:01:00.0)")
    is_discrete: bool = Field(default=False, description="True if dedicated/discrete GPU, False if integrated")
    raw_source: str = Field(default="lspci", description="Source utility (lspci, nvidia-smi)")


class MotherboardInfo(BaseModel):
    """Motherboard and system firmware (BIOS/UEFI) specifications."""

    manufacturer: str | None = Field(None, description="Motherboard/system manufacturer (e.g. Lenovo, Dell)")
    product_name: str | None = Field(None, description="Motherboard model or system product name")
    version: str | None = Field(None, description="Motherboard hardware revision")
    bios_vendor: str | None = Field(None, description="BIOS/UEFI firmware vendor")
    bios_version: str | None = Field(None, description="BIOS/UEFI firmware version string")
    bios_date: str | None = Field(None, description="BIOS release/build date")
    raw_source: str = Field(default="/sys/class/dmi/id", description="Source interface used")


class SystemSummary(BaseModel):
    """Aggregated full-system hardware overview."""

    hostname: str
    os_name: str
    kernel_release: str
    cpu: CPUInfo | None = None
    memory: MemoryInfo | None = None
    memory_topology: MemoryTopology | None = None
    storage: StorageInfo | None = None
    gpus: list[GPUInfo] = Field(default_factory=list)
    motherboard: MotherboardInfo | None = None
    inspection_timestamp: str

