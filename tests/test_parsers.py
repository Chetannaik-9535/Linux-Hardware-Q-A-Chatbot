"""Automated tests for Linux utility output parsers and normalizers."""

from unittest.mock import MagicMock, patch

from hw_assistant.inspectors.cpu import CPUInspector
from hw_assistant.inspectors.gpu import GPUInspector
from hw_assistant.inspectors.memory import MemoryInspector
from hw_assistant.inspectors.memory_topology import MemoryTopologyInspector
from hw_assistant.inspectors.motherboard import MotherboardInspector
from hw_assistant.inspectors.storage import StorageInspector
from hw_assistant.security.executor import SafeCommandExecutor


def test_cpu_parser_lscpu(thinkpad_executor):
    """Test parsing lscpu output for Intel 12th gen CPU."""
    inspector = CPUInspector(thinkpad_executor)
    info = inspector.inspect()

    assert info.vendor == "GenuineIntel"
    assert "i7-1260P" in info.model
    assert info.architecture == "x86_64"
    assert info.cores == 12
    assert info.threads == 16
    assert info.max_frequency_mhz == 4700.0
    assert info.min_frequency_mhz == 400.0
    assert info.l3_cache == "18 MiB (1 instance)"
    assert "avx2" in info.flags


def test_cpu_parser_proc_cpuinfo(thinkpad_executor):
    """Test fallback parsing of /proc/cpuinfo."""
    sample_proc = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 154
model name	: 12th Gen Intel(R) Core(TM) i7-1260P
stepping	: 3
cpu MHz		: 2100.000
physical id	: 0
core id		: 0
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6
model		: 154
model name	: 12th Gen Intel(R) Core(TM) i7-1260P
stepping	: 3
cpu MHz		: 2100.000
physical id	: 0
core id		: 1
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat
"""
    inspector = CPUInspector(thinkpad_executor)
    info = inspector._parse_proc_cpuinfo(sample_proc)

    assert info.vendor == "GenuineIntel"
    assert "i7-1260P" in info.model
    assert info.cores == 2
    assert info.threads == 2
    assert info.current_frequency_mhz == 2100.0


def test_memory_parser_free(thinkpad_executor):
    """Test parsing free -b output into gigabytes and utilization."""
    inspector = MemoryInspector(thinkpad_executor)
    info = inspector.inspect()

    assert info.total_gb == 15.38  # 16515858432 bytes / 1024^3
    assert info.used_gb == 5.7  # 6124589056 bytes
    assert info.available_gb == 9.68
    assert info.utilization_percent == 37.1
    assert info.swap_total_bytes == 8589934592


def test_memory_topology_soldered_thinkpad(thinkpad_executor):
    """Test detecting soldered RAM that cannot be upgraded."""
    inspector = MemoryTopologyInspector(thinkpad_executor)
    topo = inspector.inspect()

    assert topo.total_slots == 1
    assert topo.used_slots == 1
    assert topo.empty_slots == 0
    assert topo.is_soldered is True
    assert topo.is_upgradeable is False
    assert topo.max_capacity_gb == 16.0
    assert len(topo.modules) == 1
    assert topo.modules[0].memory_type == "LPDDR5"
    assert "Row Of Chips" in (topo.modules[0].form_factor or "")
    assert "cannot be upgraded" in topo.upgrade_assessment.lower()


def test_memory_topology_upgradeable_desktop(desktop_executor):
    """Test detecting desktop with 2 used and 2 empty DIMM slots."""
    inspector = MemoryTopologyInspector(desktop_executor)
    topo = inspector.inspect()

    assert topo.total_slots == 4
    assert topo.used_slots == 2
    assert topo.empty_slots == 2
    assert topo.is_upgradeable is True
    assert topo.is_soldered is False
    assert topo.max_capacity_gb == 128.0
    assert len(topo.modules) == 4
    assert "2 slot(s) are empty" in topo.upgrade_assessment


def test_memory_topology_socketed_replace_dell(dell_executor):
    """Test detecting socketed SODIMM laptop with all slots filled but max capacity higher."""
    inspector = MemoryTopologyInspector(dell_executor)
    topo = inspector.inspect()

    assert topo.total_slots == 2
    assert topo.used_slots == 2
    assert topo.empty_slots == 0
    assert topo.is_upgradeable is True
    assert topo.max_capacity_gb == 64.0
    assert topo.is_soldered is False
    assert "replacing the existing module" in topo.upgrade_assessment.lower()


def test_memory_topology_permission_denied():
    """Verify permission denied error reporting when dmidecode lacks root."""
    executor = SafeCommandExecutor()

    # Mock dmidecode execution returning permission denied
    sample_error = "dmidecode: /dev/mem: Permission denied"
    with patch.object(
        executor,
        "execute_command",
        return_value=MagicMock(
            exit_code=1,
            stdout="",
            stderr=sample_error,
            permission_denied=True,
            binary_not_found=False,
        ),
    ):
        inspector = MemoryTopologyInspector(executor)
        topo = inspector.inspect()

        assert topo.permission_denied is True
        assert topo.total_slots is None
        assert topo.max_capacity_gb is None
        assert "Permission denied" in topo.upgrade_assessment
        assert any("sudoers" in n for n in topo.notes)


def test_storage_parser_nvme_and_sata(desktop_executor):
    """Test storage parsing detecting both NVMe SSD and SATA HDD."""
    inspector = StorageInspector(desktop_executor)
    storage = inspector.inspect()

    assert storage.total_disks == 2
    assert storage.nvme_count == 1
    assert storage.sata_count == 1
    assert storage.ssd_count == 1
    assert storage.hdd_count == 1

    # Check first drive (NVMe SSD)
    nvme_dev = storage.devices[0]
    assert nvme_dev.name == "nvme0n1"
    assert nvme_dev.is_ssd is True
    assert nvme_dev.transport == "nvme"
    assert "Samsung SSD 980 PRO" in (nvme_dev.model or "")
    assert len(nvme_dev.children) == 2

    # Check second drive (SATA HDD)
    sata_dev = storage.devices[1]
    assert sata_dev.name == "sda"
    assert sata_dev.is_ssd is False
    assert sata_dev.rota is True
    assert sata_dev.transport == "sata"


def test_gpu_parser_dual_gpu_dell(dell_executor):
    """Test dual GPU detection: Intel integrated + NVIDIA RTX 3050 Ti with VRAM."""
    inspector = GPUInspector(dell_executor)
    gpus = inspector.inspect()

    assert len(gpus) == 2

    intel_gpu = next(g for g in gpus if g.vendor == "Intel")
    assert "Alder Lake" in intel_gpu.model
    assert intel_gpu.is_discrete is False
    assert intel_gpu.driver_version == "i915"

    nvidia_gpu = next(g for g in gpus if g.vendor == "NVIDIA")
    assert "RTX 3050 Ti" in nvidia_gpu.model
    assert nvidia_gpu.is_discrete is True
    assert nvidia_gpu.driver_version == "550.54.14"
    assert nvidia_gpu.vram_mb == 4096


def test_motherboard_parser_thinkpad(thinkpad_executor):
    """Test motherboard and BIOS parsing via sysfs."""
    inspector = MotherboardInspector(thinkpad_executor)
    mobo = inspector.inspect()

    assert mobo.manufacturer == "LENOVO"
    assert mobo.product_name == "21CBCTO1WW"
    assert "ThinkPad X1 Carbon" in (mobo.version or "")
    assert mobo.bios_vendor == "LENOVO"
    assert "N3AET75W" in (mobo.bios_version or "")
    assert mobo.bios_date == "09/18/2023"
