"""Pydantic models for tool calling schema, invocation, and execution results."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ToolName(str, Enum):
    """Allow-listed hardware inspection tool identifiers."""

    GET_CPU_INFO = "get_cpu_info"
    GET_MEMORY_INFO = "get_memory_info"
    GET_MEMORY_TOPOLOGY = "get_memory_topology"
    GET_STORAGE_INFO = "get_storage_info"
    GET_GPU_INFO = "get_gpu_info"
    GET_MOTHERBOARD_INFO = "get_motherboard_info"
    GET_SYSTEM_SUMMARY = "get_system_summary"


class ToolDefinition(BaseModel):
    """Specification of a safe tool exposed to the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_claude_tool(self) -> dict[str, Any]:
        """Convert to Anthropic Claude tool specification format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_ollama_tool(self) -> dict[str, Any]:
        """Convert to Ollama / OpenAI function format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolCallRequest(BaseModel):
    """An invocation request emitted by the LLM."""

    id: str = Field(..., description="Unique ID for this tool invocation")
    name: str = Field(..., description="Target tool function name")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Validated argument dictionary")


class ToolExecutionResult(BaseModel):
    """Result of safely running an allow-listed hardware tool."""

    tool_call_id: str
    tool_name: str
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    execution_time_ms: float = 0.0
    command_used: str | None = None
    permission_note: str | None = None


# Official Tool Definitions Registry for LLM Tool-Calling
HARDWARE_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name=ToolName.GET_CPU_INFO.value,
        description=(
            "Retrieves verified CPU specifications including manufacturer/vendor, model, architecture, "
            "number of physical cores, logical threads, clock frequencies (min/max/current), and cache sizes."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name=ToolName.GET_MEMORY_INFO.value,
        description=(
            "Retrieves real-time RAM usage statistics including total capacity, used RAM, available RAM, "
            "free RAM, utilization percentage, and swap space status from /proc/meminfo and 'free'."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name=ToolName.GET_MEMORY_TOPOLOGY.value,
        description=(
            "Inspects physical RAM slots, module types, speeds, soldered status, empty slots, and maximum "
            "motherboard supported memory capacity using dmidecode. Use this to determine if RAM can be upgraded."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name=ToolName.GET_STORAGE_INFO.value,
        description=(
            "Retrieves storage device details including disk models, sizes, drive types (SSD vs HDD), "
            "bus transport protocol (NVMe vs SATA), mountpoints, and partition layout using lsblk."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name=ToolName.GET_GPU_INFO.value,
        description=(
            "Retrieves graphics processing unit (GPU) information including vendor (NVIDIA, AMD, Intel), "
            "model name, driver version, VRAM capacity, and whether it is integrated or dedicated."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name=ToolName.GET_MOTHERBOARD_INFO.value,
        description=(
            "Retrieves motherboard/system manufacturer, product model, and BIOS/UEFI firmware version "
            "and release date from /sys/class/dmi/id and dmidecode."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolDefinition(
        name=ToolName.GET_SYSTEM_SUMMARY.value,
        description=(
            "Retrieves a comprehensive snapshot of all system hardware components: OS, Kernel, CPU, "
            "RAM, Storage, GPU, and Motherboard in a single call."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]

TOOL_REGISTRY: dict[str, ToolDefinition] = {t.name: t for t in HARDWARE_TOOLS}

