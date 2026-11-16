"""Strict allow-list registry and command specifications for safe Linux inspection."""

from __future__ import annotations

import shutil
from typing import NamedTuple


class CommandSpec(NamedTuple):
    """Specification of an immutable, allow-listed system command."""

    binary_name: str
    args: list[str]
    timeout_seconds: float = 5.0
    requires_root: bool = False
    preferred_path: str | None = None
    description: str = ""


# Immutable command dictionary mapping internal keys to fixed binary and arg lists.
# Absolutely no user or LLM input can be appended to or substitute these arguments.
ALLOWLISTED_COMMANDS: dict[str, CommandSpec] = {
    "lscpu": CommandSpec(
        binary_name="lscpu",
        args=["lscpu"],
        timeout_seconds=5.0,
        preferred_path="/usr/bin/lscpu",
        description="Extract CPU architecture, cores, threads, and frequency",
    ),
    "free": CommandSpec(
        binary_name="free",
        args=["free", "-b"],
        timeout_seconds=5.0,
        preferred_path="/usr/bin/free",
        description="Extract real-time RAM and swap metrics in exact bytes",
    ),
    "lsblk": CommandSpec(
        binary_name="lsblk",
        args=["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL,ROTA,TRAN,FSTYPE"],
        timeout_seconds=5.0,
        preferred_path="/usr/bin/lsblk",
        description="Inspect block devices, disks, partitions, and rotational SSD/HDD flags as JSON",
    ),
    "lspci": CommandSpec(
        binary_name="lspci",
        args=["lspci", "-nnmm"],
        timeout_seconds=5.0,
        preferred_path="/usr/bin/lspci",
        description="List PCI bus hardware devices and vendor/device IDs",
    ),
    "lspci_driver": CommandSpec(
        binary_name="lspci",
        args=["lspci", "-k"],
        timeout_seconds=5.0,
        preferred_path="/usr/bin/lspci",
        description="List PCI devices with kernel drivers in use",
    ),
    "nvidia_smi": CommandSpec(
        binary_name="nvidia-smi",
        args=[
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total,pci.bus_id",
            "--format=csv,noheader,nounits",
        ],
        timeout_seconds=5.0,
        preferred_path="/usr/bin/nvidia-smi",
        description="Query NVIDIA proprietary driver for GPU model, VRAM, and driver release",
    ),
    "dmidecode_memory": CommandSpec(
        binary_name="dmidecode",
        args=["dmidecode", "-t", "memory"],
        timeout_seconds=5.0,
        requires_root=True,
        preferred_path="/usr/sbin/dmidecode",
        description="Inspect physical RAM slots, module types, speeds, and max motherboard capacity",
    ),
    "dmidecode_baseboard": CommandSpec(
        binary_name="dmidecode",
        args=["dmidecode", "-t", "baseboard,bios"],
        timeout_seconds=5.0,
        requires_root=True,
        preferred_path="/usr/sbin/dmidecode",
        description="Inspect motherboard product name and BIOS version",
    ),
}


def resolve_binary_path(binary_name: str, preferred_path: str | None = None) -> str | None:
    """Safely locate the exact binary path on the host filesystem."""
    # Check preferred standard system paths first
    if preferred_path and shutil.which(preferred_path):
        return preferred_path

    # Fallback to standard PATH search
    found = shutil.which(binary_name)
    if found:
        return found

    # Check common system bin locations if not on standard PATH
    common_locations = [
        f"/usr/bin/{binary_name}",
        f"/bin/{binary_name}",
        f"/usr/sbin/{binary_name}",
        f"/sbin/{binary_name}",
    ]
    for loc in common_locations:
        if shutil.which(loc):
            return loc

    return None

