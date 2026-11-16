"""GPU hardware inspector using lspci and nvidia-smi."""

from __future__ import annotations

import re
from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.models.hardware import GPUInfo


class GPUInspector(BaseInspector):
    """Inspector for graphics cards, display controllers, VRAM, and GPU drivers."""

    def inspect(self) -> list[GPUInfo]:
        """Detect GPUs via lspci with nvidia-smi cross-referencing."""
        gpus: list[GPUInfo] = []

        # 1. Query lspci -nnmm
        pci_res = self.executor.execute_command("lspci")
        driver_res = self.executor.execute_command("lspci_driver")

        drivers_by_slot = self._parse_drivers_by_slot(driver_res.stdout) if driver_res.exit_code == 0 else {}

        if pci_res.exit_code == 0 and pci_res.stdout.strip():
            gpus = self._parse_lspci_nnmm(pci_res.stdout, drivers_by_slot)

        # 2. Query nvidia-smi for NVIDIA GPUs (provides exact VRAM and driver)
        nvidia_res = self.executor.execute_command("nvidia_smi")
        if nvidia_res.exit_code == 0 and nvidia_res.stdout.strip():
            self._enrich_with_nvidia_smi(gpus, nvidia_res.stdout)

        # 3. If no GPU detected from lspci, check nvidia-smi directly
        if not gpus and nvidia_res.exit_code == 0 and nvidia_res.stdout.strip():
            gpus = self._parse_nvidia_smi_standalone(nvidia_res.stdout)

        return gpus

    def _parse_lspci_nnmm(self, stdout: str, drivers: dict[str, str]) -> list[GPUInfo]:
        """Parse 'lspci -nnmm' device records for display/VGA controllers."""
        slots = stdout.strip().split("\n\n")
        gpus: list[GPUInfo] = []

        for record in slots:
            lines = record.strip().splitlines()
            dev_dict: dict[str, str] = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    dev_dict[k.strip()] = v.strip()

            slot = dev_dict.get("Slot", "")
            cls = dev_dict.get("Class", "")
            vendor = dev_dict.get("Vendor", "")
            device = dev_dict.get("Device", "")
            sdevice = dev_dict.get("SDevice", "")

            # Check if this PCI device is a Display, VGA, or 3D controller
            cls_lower = cls.lower()
            if any(term in cls_lower for term in ("vga", "3d", "display")):
                # Determine vendor
                vendor_clean = self._clean_vendor(vendor)

                # Clean model name
                model_clean = device.strip('"')
                if sdevice and sdevice.strip('"') not in model_clean:
                    model_clean = f"{model_clean} ({sdevice.strip('\"')})"

                # Determine if discrete
                is_discrete = any(d in cls_lower for d in ("3d controller", "3d")) or (
                    "nvidia" in vendor_clean.lower() and "geforce" in model_clean.lower()
                )

                driver = drivers.get(slot)

                gpus.append(
                    GPUInfo(
                        vendor=vendor_clean,
                        model=model_clean,
                        driver_version=driver,
                        vram_mb=None,  # Will be populated by nvidia-smi or remains None
                        pcie_slot=slot or None,
                        is_discrete=is_discrete,
                        raw_source="lspci",
                    )
                )

        return gpus

    def _parse_drivers_by_slot(self, stdout: str) -> dict[str, str]:
        """Extract 'Kernel driver in use' keyed by slot from 'lspci -k'."""
        drivers: dict[str, str] = {}
        current_slot: str | None = None

        for line in stdout.splitlines():
            # e.g., '00:02.0 VGA compatible controller...'
            slot_match = re.match(r"^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F])", line)
            if slot_match:
                current_slot = slot_match.group(1)
            elif current_slot and "Kernel driver in use:" in line:
                driver_name = line.split("Kernel driver in use:", 1)[1].strip()
                drivers[current_slot] = driver_name

        return drivers

    def _enrich_with_nvidia_smi(self, gpus: list[GPUInfo], stdout: str) -> None:
        """Enrich existing GPU entries with exact VRAM and driver from nvidia-smi."""
        # Output format: name, driver_version, memory.total, pci.bus_id
        for line in stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 3:
                name = parts[0]
                driver = parts[1]
                try:
                    vram_mb = int(parts[2])
                except ValueError:
                    vram_mb = None

                matched = False
                for gpu in gpus:
                    if gpu.vendor.lower() == "nvidia":
                        gpu.model = name
                        gpu.driver_version = driver
                        gpu.vram_mb = vram_mb
                        gpu.is_discrete = True
                        gpu.raw_source = "lspci+nvidia-smi"
                        matched = True
                        break

                if not matched:
                    gpus.append(
                        GPUInfo(
                            vendor="NVIDIA",
                            model=name,
                            driver_version=driver,
                            vram_mb=vram_mb,
                            is_discrete=True,
                            raw_source="nvidia-smi",
                        )
                    )

    def _parse_nvidia_smi_standalone(self, stdout: str) -> list[GPUInfo]:
        """Build GPUInfo list directly from nvidia-smi output if lspci was empty."""
        gpus: list[GPUInfo] = []
        for line in stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 3:
                try:
                    vram_mb = int(parts[2])
                except ValueError:
                    vram_mb = None
                gpus.append(
                    GPUInfo(
                        vendor="NVIDIA",
                        model=parts[0],
                        driver_version=parts[1],
                        vram_mb=vram_mb,
                        is_discrete=True,
                        raw_source="nvidia-smi",
                    )
                )
        return gpus

    @staticmethod
    def _clean_vendor(raw: str) -> str:
        """Standardize vendor string."""
        s = raw.strip('"')
        lower = s.lower()
        if "intel" in lower:
            return "Intel"
        if "nvidia" in lower:
            return "NVIDIA"
        if "amd" in lower or "advanced micro" in lower or "ati" in lower:
            return "AMD"
        return s

