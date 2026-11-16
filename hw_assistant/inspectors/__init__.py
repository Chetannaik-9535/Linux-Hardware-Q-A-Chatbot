"""Hardware inspectors package."""

from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.inspectors.cpu import CPUInspector
from hw_assistant.inspectors.gpu import GPUInspector
from hw_assistant.inspectors.memory import MemoryInspector
from hw_assistant.inspectors.memory_topology import MemoryTopologyInspector
from hw_assistant.inspectors.motherboard import MotherboardInspector
from hw_assistant.inspectors.storage import StorageInspector
from hw_assistant.inspectors.system import SystemSummaryInspector

__all__ = [
    "BaseInspector",
    "CPUInspector",
    "MemoryInspector",
    "MemoryTopologyInspector",
    "StorageInspector",
    "GPUInspector",
    "MotherboardInspector",
    "SystemSummaryInspector",
]

