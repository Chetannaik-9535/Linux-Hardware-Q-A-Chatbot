"""Storage hardware inspector using lsblk -J."""

from __future__ import annotations

import json
from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.models.hardware import BlockDevice, StorageInfo


class StorageInspector(BaseInspector):
    """Inspector for disk drives, SSD/HDD classification, bus transports, and partitions."""

    def inspect(self) -> StorageInfo:
        """Inspect storage hierarchy via lsblk -J."""
        result = self.executor.execute_command("lsblk")
        if result.exit_code == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                raw_devices = data.get("blockdevices", [])
                return self._parse_blockdevices(raw_devices)
            except Exception:
                pass

        # Fallback if lsblk failed
        return StorageInfo(
            devices=[],
            total_disks=0,
            ssd_count=0,
            hdd_count=0,
            nvme_count=0,
            sata_count=0,
            raw_source="none",
        )

    def _parse_blockdevices(self, raw_list: list[dict]) -> StorageInfo:
        """Recursively parse lsblk JSON blocks into validated BlockDevice models."""
        parsed_devices: list[BlockDevice] = []
        ssd_count = 0
        hdd_count = 0
        nvme_count = 0
        sata_count = 0
        disk_count = 0

        for item in raw_list:
            dev = self._build_device(item)
            # Only include top-level disks, loop devices, or roms
            parsed_devices.append(dev)

            # Summaries for physical disk drives
            dev_type = (dev.type or "").lower()
            if dev_type == "disk":
                disk_count += 1
                if dev.is_ssd is True:
                    ssd_count += 1
                elif dev.is_ssd is False:
                    hdd_count += 1

                tran = (dev.transport or "").lower()
                if "nvme" in tran or "nvme" in dev.name.lower():
                    nvme_count += 1
                elif "sata" in tran or "ata" in tran:
                    sata_count += 1

        return StorageInfo(
            devices=parsed_devices,
            total_disks=disk_count,
            ssd_count=ssd_count,
            hdd_count=hdd_count,
            nvme_count=nvme_count,
            sata_count=sata_count,
            raw_source="lsblk",
        )

    def _build_device(self, item: dict) -> BlockDevice:
        """Convert a single lsblk node and its children into a BlockDevice."""
        name = item.get("name", "unknown")
        size = item.get("size", "0B")
        dev_type = item.get("type", "unknown")
        mountpoint = item.get("mountpoint")
        model = (item.get("model") or "").strip() or None
        tran = item.get("tran")
        fstype = item.get("fstype")

        # Rotational flag: True = HDD (spinning), False = SSD (solid state)
        rota_val = item.get("rota")
        rota: bool | None = None
        is_ssd: bool | None = None

        if rota_val is not None:
            if isinstance(rota_val, bool):
                rota = rota_val
            elif isinstance(rota_val, str):
                rota = rota_val.strip() in ("1", "true", "True")
            elif isinstance(rota_val, (int, float)):
                rota = bool(rota_val)
            is_ssd = not rota

        # Infer NVMe transport if in device name (e.g., nvme0n1)
        if not tran and name.startswith("nvme"):
            tran = "nvme"

        children_raw = item.get("children", [])
        children = [self._build_device(child) for child in children_raw]

        return BlockDevice(
            name=name,
            size=size,
            type=dev_type,
            mountpoint=mountpoint,
            model=model,
            rota=rota,
            is_ssd=is_ssd,
            transport=tran,
            fstype=fstype,
            children=children,
        )

