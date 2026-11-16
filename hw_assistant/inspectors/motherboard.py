"""Motherboard and BIOS/UEFI firmware inspector."""

from __future__ import annotations

from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.models.hardware import MotherboardInfo


class MotherboardInspector(BaseInspector):
    """Inspector for motherboard manufacturer, product model, and BIOS/UEFI details."""

    def inspect(self) -> MotherboardInfo:
        """Inspect motherboard and firmware using unprivileged /sys/class/dmi/id first."""
        # 1. Unprivileged sysfs read (/sys/class/dmi/id/)
        mfg = self._read_dmi_file("board_vendor") or self._read_dmi_file("sys_vendor")
        prod = self._read_dmi_file("board_name") or self._read_dmi_file("product_name")
        version = self._read_dmi_file("product_version")
        bios_vendor = self._read_dmi_file("bios_vendor")
        bios_version = self._read_dmi_file("bios_version")
        bios_date = self._read_dmi_file("bios_date")

        if mfg or prod or bios_version:
            return MotherboardInfo(
                manufacturer=mfg,
                product_name=prod,
                version=version,
                bios_vendor=bios_vendor,
                bios_version=bios_version,
                bios_date=bios_date,
                raw_source="/sys/class/dmi/id",
            )

        # 2. Fallback to dmidecode -t baseboard,bios
        dmi_res = self.executor.execute_command("dmidecode_baseboard")
        if dmi_res.exit_code == 0 and dmi_res.stdout.strip():
            return self._parse_dmidecode_baseboard(dmi_res.stdout)

        # 3. Minimal fallback
        return MotherboardInfo(
            manufacturer="Unknown",
            product_name="Unknown Motherboard",
            bios_vendor="Unknown",
            bios_version="Unknown",
            bios_date=None,
            raw_source="none",
        )

    def _read_dmi_file(self, filename: str) -> str | None:
        """Safely read a single file under /sys/class/dmi/id/."""
        content, err = self.executor.read_sysfs_or_proc(f"/sys/class/dmi/id/{filename}")
        if content and content.strip():
            clean = content.strip()
            # Filter dummy strings often reported by generic OEMs
            if clean in ("None", "Default string", "To be filled by O.E.M.", "System Serial Number"):
                return None
            return clean
        return None

    def _parse_dmidecode_baseboard(self, stdout: str) -> MotherboardInfo:
        """Parse 'dmidecode -t baseboard,bios' text."""
        sections = stdout.split("Handle ")
        mfg = None
        prod = None
        version = None
        bios_vendor = None
        bios_version = None
        bios_date = None

        for sec in sections:
            if "Base Board Information" in sec or "DMI type 2" in sec:
                for line in sec.splitlines():
                    if line.strip().startswith("Manufacturer:"):
                        mfg = line.split(":", 1)[1].strip()
                    elif line.strip().startswith("Product Name:"):
                        prod = line.split(":", 1)[1].strip()
                    elif line.strip().startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
            elif "BIOS Information" in sec or "DMI type 0" in sec:
                for line in sec.splitlines():
                    if line.strip().startswith("Vendor:"):
                        bios_vendor = line.split(":", 1)[1].strip()
                    elif line.strip().startswith("Version:"):
                        bios_version = line.split(":", 1)[1].strip()
                    elif line.strip().startswith("Release Date:"):
                        bios_date = line.split(":", 1)[1].strip()

        return MotherboardInfo(
            manufacturer=mfg,
            product_name=prod,
            version=version,
            bios_vendor=bios_vendor,
            bios_version=bios_version,
            bios_date=bios_date,
            raw_source="dmidecode",
        )

