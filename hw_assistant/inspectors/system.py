"""Aggregated system hardware summary inspector."""

from __future__ import annotations

import datetime
import platform

from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.inspectors.cpu import CPUInspector
from hw_assistant.inspectors.gpu import GPUInspector
from hw_assistant.inspectors.memory import MemoryInspector
from hw_assistant.inspectors.memory_topology import MemoryTopologyInspector
from hw_assistant.inspectors.motherboard import MotherboardInspector
from hw_assistant.inspectors.storage import StorageInspector
from hw_assistant.models.hardware import SystemSummary


class SystemSummaryInspector(BaseInspector):
    """Aggregates all hardware components into a unified snapshot."""

    def inspect(self) -> SystemSummary:
        """Inspect all system subsystems and construct SystemSummary."""
        cpu = CPUInspector(self.executor).inspect()
        mem = MemoryInspector(self.executor).inspect()
        topo = MemoryTopologyInspector(self.executor).inspect()
        storage = StorageInspector(self.executor).inspect()
        gpus = GPUInspector(self.executor).inspect()
        mobo = MotherboardInspector(self.executor).inspect()

        return SystemSummary(
            hostname=platform.node() or "linux-host",
            os_name=platform.platform() or "Linux",
            kernel_release=platform.release() or "unknown",
            cpu=cpu,
            memory=mem,
            memory_topology=topo,
            storage=storage,
            gpus=gpus,
            motherboard=mobo,
            inspection_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

