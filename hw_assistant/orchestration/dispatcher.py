"""Safe tool dispatcher connecting LLM tool calls to hardware inspectors."""

from __future__ import annotations

import time
from typing import Any

from hw_assistant.inspectors.cpu import CPUInspector
from hw_assistant.inspectors.gpu import GPUInspector
from hw_assistant.inspectors.memory import MemoryInspector
from hw_assistant.inspectors.memory_topology import MemoryTopologyInspector
from hw_assistant.inspectors.motherboard import MotherboardInspector
from hw_assistant.inspectors.storage import StorageInspector
from hw_assistant.inspectors.system import SystemSummaryInspector
from hw_assistant.models.tools import (
    TOOL_REGISTRY,
    ToolCallRequest,
    ToolExecutionResult,
    ToolName,
)
from hw_assistant.security.executor import SafeCommandExecutor, default_executor


class ToolDispatcher:
    """Safe dispatcher that rejects unauthorized tools and runs verified inspectors."""

    def __init__(self, executor: SafeCommandExecutor | None = None) -> None:
        self.executor = executor or default_executor

    def execute_tool_call(self, call: ToolCallRequest) -> ToolExecutionResult:
        """Execute a tool call request safely and return structured ToolExecutionResult."""
        start = time.perf_counter()

        # 1. ALLOW-LIST VERIFICATION: Reject unknown or injected tool names
        if call.name not in TOOL_REGISTRY:
            duration = (time.perf_counter() - start) * 1000.0
            return ToolExecutionResult(
                tool_call_id=call.id,
                tool_name=call.name,
                success=False,
                error=f"Security rejection: Tool '{call.name}' is not in the allow-list.",
                execution_time_ms=round(duration, 2),
            )

        # 2. DISPATCH TO DEDICATED INSPECTOR
        try:
            data, perm_note = self._dispatch(call.name)
            duration = (time.perf_counter() - start) * 1000.0
            return ToolExecutionResult(
                tool_call_id=call.id,
                tool_name=call.name,
                success=True,
                data=data,
                execution_time_ms=round(duration, 2),
                permission_note=perm_note,
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            return ToolExecutionResult(
                tool_call_id=call.id,
                tool_name=call.name,
                success=False,
                error=f"Error executing inspection: {str(e)}",
                execution_time_ms=round(duration, 2),
            )

    def _dispatch(self, tool_name: str) -> tuple[dict[str, Any], str | None]:
        """Route to appropriate inspector and serialize to dictionary."""
        perm_note = None

        if tool_name == ToolName.GET_CPU_INFO.value:
            res = CPUInspector(self.executor).inspect()
            return res.model_dump(), None

        elif tool_name == ToolName.GET_MEMORY_INFO.value:
            res = MemoryInspector(self.executor).inspect()
            return res.model_dump(), None

        elif tool_name == ToolName.GET_MEMORY_TOPOLOGY.value:
            res = MemoryTopologyInspector(self.executor).inspect()
            if res.permission_denied:
                perm_note = "Elevated privileges required for full DMI topology."
            return res.model_dump(), perm_note

        elif tool_name == ToolName.GET_STORAGE_INFO.value:
            res = StorageInspector(self.executor).inspect()
            return res.model_dump(), None

        elif tool_name == ToolName.GET_GPU_INFO.value:
            res_list = GPUInspector(self.executor).inspect()
            return {"gpus": [g.model_dump() for g in res_list]}, None

        elif tool_name == ToolName.GET_MOTHERBOARD_INFO.value:
            res = MotherboardInspector(self.executor).inspect()
            return res.model_dump(), None

        elif tool_name == ToolName.GET_SYSTEM_SUMMARY.value:
            res = SystemSummaryInspector(self.executor).inspect()
            return res.model_dump(), None

        raise ValueError(f"Unhandled tool name: {tool_name}")

