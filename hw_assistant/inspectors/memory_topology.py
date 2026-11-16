"""Memory topology and physical RAM slot inspector using dmidecode."""

from __future__ import annotations

import re
from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.models.hardware import MemoryModule, MemoryTopology


class MemoryTopologyInspector(BaseInspector):
    """Inspector for motherboard physical RAM slots, modules, and upgrade limits."""

    def inspect(self) -> MemoryTopology:
        """Inspect physical memory topology via dmidecode -t memory."""
        result = self.executor.execute_command("dmidecode_memory")

        # 1. Handle permission denial or missing root
        if result.permission_denied:
            return MemoryTopology(
                total_slots=None,
                used_slots=None,
                empty_slots=None,
                modules=[],
                max_capacity_gb=None,
                is_upgradeable=None,
                is_soldered=None,
                upgrade_assessment=(
                    "Permission denied: Deep hardware topology inspection (dmidecode) requires root/sudo privileges. "
                    "Cannot verify physical RAM slots or motherboard limits without access."
                ),
                permission_denied=True,
                notes=[
                    "Insufficient privileges to access DMI/SMBIOS memory tables.",
                    "To enable safe read-only inspection, configure a scoped sudoers rule: "
                    "'<user> ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode -t memory'",
                ],
            )

        # 2. Handle missing utility
        if result.binary_not_found or result.exit_code != 0:
            return MemoryTopology(
                total_slots=None,
                used_slots=None,
                empty_slots=None,
                modules=[],
                max_capacity_gb=None,
                is_upgradeable=None,
                is_soldered=None,
                upgrade_assessment="System utility 'dmidecode' is not available on this machine.",
                permission_denied=False,
                notes=["Utility dmidecode not found or execution failed."],
            )

        # 3. Parse dmidecode -t memory output
        return self._parse_dmidecode_memory(result.stdout)

    def _parse_dmidecode_memory(self, stdout: str) -> MemoryTopology:
        """Parse DMI type 16 (Physical Memory Array) and type 17 (Memory Device) records."""
        # Split by Handle
        handles = stdout.split("Handle ")

        max_capacity_gb: float | None = None
        array_slot_count: int | None = None
        modules: list[MemoryModule] = []

        for section in handles:
            if not section.strip():
                continue

            lines = section.splitlines()
            header = lines[0] if lines else ""

            # Check for DMI Type 16: Physical Memory Array
            if "DMI type 16" in header or "Physical Memory Array" in section:
                for line in lines:
                    line_s = line.strip()
                    if line_s.startswith("Maximum Capacity:"):
                        val_str = line_s.split(":", 1)[1].strip()
                        max_capacity_gb = self._parse_capacity_string(val_str)
                    elif line_s.startswith("Number Of Devices:"):
                        try:
                            array_slot_count = int(line_s.split(":", 1)[1].strip())
                        except ValueError:
                            pass

            # Check for DMI Type 17: Memory Device
            elif "DMI type 17" in header or "Memory Device" in section:
                mod_data: dict[str, str] = {}
                for line in lines:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        mod_data[k.strip()] = v.strip()

                locator = mod_data.get("Locator", f"Slot {len(modules) + 1}")
                size_str = mod_data.get("Size", "Unknown")
                form_factor = mod_data.get("Form Factor")
                mem_type = mod_data.get("Type")
                speed_str = mod_data.get("Configured Memory Speed") or mod_data.get("Speed")
                manufacturer = mod_data.get("Manufacturer")
                part_number = mod_data.get("Part Number")

                # Detect if module is installed
                installed = not (
                    "no module installed" in size_str.lower()
                    or size_str.strip() in ("", "Not Installed", "0 MB", "0 GB")
                )

                size_gb = self._parse_capacity_string(size_str) if installed else None
                speed_mhz = self._parse_speed_mhz(speed_str)

                # Filter placeholder values
                if manufacturer in ("Not Specified", "NO DIMM", "None", "Unknown"):
                    manufacturer = None
                if part_number in ("Not Specified", "NO DIMM", "None", "Unknown"):
                    part_number = None
                if mem_type in ("Unknown", "None"):
                    mem_type = None

                modules.append(
                    MemoryModule(
                        locator=locator,
                        installed=installed,
                        size_raw=size_str,
                        size_gb=size_gb,
                        memory_type=mem_type,
                        speed_mhz=speed_mhz,
                        manufacturer=manufacturer,
                        part_number=part_number,
                        form_factor=form_factor,
                    )
                )

        # Totals calculation
        total_slots = array_slot_count if array_slot_count is not None else len(modules)
        used_slots = sum(1 for m in modules if m.installed)
        empty_slots = max(0, total_slots - used_slots) if total_slots >= used_slots else 0

        # Current total installed RAM in modules
        installed_gb = sum(m.size_gb for m in modules if m.size_gb is not None)

        # Detect soldered memory
        is_soldered = any(
            (m.form_factor and "row of chips" in m.form_factor.lower())
            or (m.memory_type and "lpddr" in m.memory_type.lower())
            for m in modules
            if m.installed
        )

        # Upgradeability assessment
        is_upgradeable = False
        notes: list[str] = []

        if is_soldered and empty_slots == 0:
            is_upgradeable = False
            upgrade_assessment = (
                f"Memory is soldered directly to the motherboard ({modules[0].memory_type or 'LPDDR'}, "
                f"{installed_gb:.0f} GB). There are no expansion slots; RAM cannot be upgraded."
            )
            notes.append("Soldered memory architecture detected (Row of chips / LPDDR).")
        elif empty_slots > 0:
            is_upgradeable = True
            max_info = f" Motherboard supports up to {max_capacity_gb:.0f} GB." if max_capacity_gb else ""
            upgrade_assessment = (
                f"RAM can be upgraded. You have {used_slots} of {total_slots} slots used with {installed_gb:.0f} GB installed. "
                f"{empty_slots} slot(s) are empty and available.{max_info}"
            )
        else:
            # All slots are filled, but are they socketed DIMMs/SODIMMs that can be swapped for larger sticks?
            socketed = any(
                m.form_factor and m.form_factor.lower() in ("sodimm", "dimm")
                for m in modules
                if m.installed
            )
            if socketed and max_capacity_gb and installed_gb < max_capacity_gb:
                is_upgradeable = True
                upgrade_assessment = (
                    f"All {total_slots} memory slots are currently occupied ({installed_gb:.0f} GB installed), "
                    f"but the motherboard supports up to {max_capacity_gb:.0f} GB. You can upgrade by replacing "
                    "the existing module(s) with higher-capacity sticks."
                )
            elif socketed and max_capacity_gb and installed_gb >= max_capacity_gb:
                is_upgradeable = False
                upgrade_assessment = (
                    f"All {total_slots} slots are populated ({installed_gb:.0f} GB installed), which is already "
                    f"at the motherboard's maximum supported capacity of {max_capacity_gb:.0f} GB."
                )
            elif socketed and max_capacity_gb is None:
                is_upgradeable = True
                upgrade_assessment = (
                    f"All {total_slots} slot(s) are populated ({installed_gb:.0f} GB installed). "
                    "Modules are socketed and may be replaced, but maximum motherboard capacity could not be verified."
                )
            else:
                is_upgradeable = False
                upgrade_assessment = (
                    f"Memory configuration: {used_slots} of {total_slots} slots populated. Upgrade potential indeterminate."
                )

        return MemoryTopology(
            total_slots=total_slots,
            used_slots=used_slots,
            empty_slots=empty_slots,
            modules=modules,
            max_capacity_gb=max_capacity_gb,
            is_upgradeable=is_upgradeable,
            is_soldered=is_soldered,
            upgrade_assessment=upgrade_assessment,
            permission_denied=False,
            notes=notes,
        )

    @staticmethod
    def _parse_capacity_string(val: str) -> float | None:
        """Parse capacity strings like '16 GB', '512 MB', '1 TB' into float GB."""
        if not val or "unknown" in val.lower() or "no module" in val.lower():
            return None

        match = re.search(r"(\d+(?:\.\d+)?)\s*([KMGTP]?B)", val, re.IGNORECASE)
        if not match:
            return None

        number = float(match.group(1))
        unit = match.group(2).upper()

        if unit in ("B", "BYTES"):
            return round(number / (1024**3), 2)
        elif unit in ("KB", "KIB"):
            return round(number / (1024**2), 2)
        elif unit in ("MB", "MIB"):
            return round(number / 1024, 2)
        elif unit in ("GB", "GIB"):
            return round(number, 2)
        elif unit in ("TB", "TIB"):
            return round(number * 1024, 2)
        return round(number, 2)

    @staticmethod
    def _parse_speed_mhz(val: str | None) -> int | None:
        """Parse clock rate string like '4800 MT/s' or '3200 MHz'."""
        if not val or "unknown" in val.lower():
            return None
        match = re.search(r"(\d+)", val)
        if match:
            return int(match.group(1))
        return None

