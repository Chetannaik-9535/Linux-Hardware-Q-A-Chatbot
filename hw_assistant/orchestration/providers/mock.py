"""Intelligent deterministic mock provider for tests, offline demos, and verification."""

from __future__ import annotations

import uuid
from typing import Any

from hw_assistant.models.chat import ChatMessage
from hw_assistant.models.tools import ToolCallRequest, ToolDefinition, ToolName
from hw_assistant.orchestration.providers.base import BaseLLMProvider, ProviderResponse


class MockProvider(BaseLLMProvider):
    """Deterministic LLM simulator that parses queries, triggers tools, and formats verified answers."""

    def generate(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> ProviderResponse:
        """Simulate LLM tool-calling decision or answer synthesis based on conversation state."""
        # Check if the latest message contains tool results to synthesize an answer from
        if messages and messages[-1].role == "tool" and messages[-1].tool_results:
            return self._synthesize_answer_from_tools(messages[-1].tool_results)

        # Otherwise, parse the latest user question and select appropriate tools
        last_user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m.content.lower()
                break

        tool_calls = self._select_tools_for_query(last_user_msg)
        if tool_calls:
            return ProviderResponse(content=None, tool_calls=tool_calls)

        # Fallback response for unhandled general questions
        return ProviderResponse(
            content=(
                "I am your local Linux Hardware Assistant. You can ask me questions such as:\n"
                "- How much RAM do I have?\n"
                "- Can I upgrade my RAM?\n"
                "- What CPU am I using?\n"
                "- Is my SSD NVMe or SATA?\n"
                "- What GPU is installed?\n"
                "- Give me a full system summary."
            ),
            tool_calls=[],
        )

    def _select_tools_for_query(self, query: str) -> list[ToolCallRequest]:
        """Map user query intent to one or more allow-listed tools."""
        calls: list[ToolCallRequest] = []

        is_summary = any(kw in query for kw in ("system summary", "full spec", "overview", "all hardware", "about my machine"))
        if is_summary:
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_SYSTEM_SUMMARY.value))
            return calls

        # RAM upgrade, slot, or maximum capacity questions
        upgrade_keywords = (
            "upgrade",
            "slot",
            "maximum capacity",
            "max capacity",
            "maximum supported",
            "supported capacity",
            "ram capacity",
            "max ram",
            "add ram",
            "more ram",
            "slots",
        )
        is_upgrade = any(kw in query for kw in upgrade_keywords)
        if is_upgrade:
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_MEMORY_TOPOLOGY.value))
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_MEMORY_INFO.value))
            return calls

        # General RAM / memory questions
        is_ram = any(kw in query for kw in ("ram", "memory", "free memory", "used memory", "swap"))
        if is_ram:
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_MEMORY_INFO.value))

        # CPU / processor questions
        is_cpu = any(kw in query for kw in ("cpu", "processor", "core", "thread", "frequency", "ghz", "mhz", "intel", "amd", "ryzen", "i7", "i5"))
        if is_cpu:
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_CPU_INFO.value))

        # Storage / SSD / NVMe / HDD questions
        is_storage = any(kw in query for kw in ("ssd", "hdd", "nvme", "sata", "disk", "storage", "drive", "hard drive", "partition"))
        if is_storage:
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_STORAGE_INFO.value))

        # GPU / graphics questions
        is_gpu = any(kw in query for kw in ("gpu", "graphics", "video card", "vram", "nvidia", "rtx", "geforce", "radeon"))
        if is_gpu:
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_GPU_INFO.value))

        # Motherboard / BIOS questions
        is_mobo = any(kw in query for kw in ("motherboard", "bios", "uefi", "board", "firmware", "baseboard"))
        if is_mobo:
            calls.append(ToolCallRequest(id=f"call_{uuid.uuid4().hex[:6]}", name=ToolName.GET_MOTHERBOARD_INFO.value))

        return calls

    def _synthesize_answer_from_tools(self, results: list[Any]) -> ProviderResponse:
        """Synthesize a factual, grounded response from executed tool results."""
        answers: list[str] = []

        data_map = {res.tool_name: res.data for res in results if res.success and res.data}

        # 1. Memory Topology & Upgradeability
        if ToolName.GET_MEMORY_TOPOLOGY.value in data_map:
            topo = data_map[ToolName.GET_MEMORY_TOPOLOGY.value]
            mem = data_map.get(ToolName.GET_MEMORY_INFO.value, {})

            if topo.get("permission_denied"):
                answers.append(
                    f"⚠️ **Permission Notice:** {topo.get('upgrade_assessment')}\n\n"
                    "To allow non-root memory topology inspection, add this rule to `/etc/sudoers.d/hw-assistant`:\n"
                    "```bash\n<username> ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode -t memory\n```"
                )
            else:
                total_slots = topo.get("total_slots")
                used_slots = topo.get("used_slots")
                empty_slots = topo.get("empty_slots")
                max_cap = topo.get("max_capacity_gb")
                is_soldered = topo.get("is_soldered")
                is_upgradeable = topo.get("is_upgradeable")

                total_gb = mem.get("total_gb") or sum(
                    m.get("size_gb", 0) for m in topo.get("modules", []) if m.get("size_gb")
                )

                if is_soldered and empty_slots == 0:
                    answers.append(
                        f"**RAM Upgrade Assessment:** No, you **cannot upgrade your RAM**.\n"
                        f"- **Installed Memory:** {total_gb:.1f} GB soldered directly to the motherboard (`Row of chips`).\n"
                        f"- **Slots:** {used_slots} of {total_slots} populated (0 empty slots).\n"
                        f"- **Form Factor:** Soldered LPDDR; there are no SODIMM expansion sockets available."
                    )
                elif is_upgradeable and empty_slots and empty_slots > 0:
                    max_txt = f" up to **{max_cap:.0f} GB**" if max_cap else " (maximum capacity not specified by BIOS)"
                    answers.append(
                        f"**RAM Upgrade Assessment:** Yes, you **can upgrade your RAM**!\n"
                        f"- **Installed Memory:** {total_gb:.1f} GB across {used_slots} populated slot(s).\n"
                        f"- **Physical Slots:** {total_slots} total slots ({empty_slots} empty slot(s) currently available).\n"
                        f"- **Maximum Supported Capacity:** The motherboard supports{max_txt}."
                    )
                elif is_upgradeable and empty_slots == 0:
                    answers.append(
                        f"**RAM Upgrade Assessment:** Yes, you **can upgrade by replacing existing modules**.\n"
                        f"- **Installed Memory:** {total_gb:.1f} GB occupying all {total_slots} slot(s).\n"
                        f"- **Slots:** Modules are removable socketed SODIMMs/DIMMs.\n"
                        f"- **Maximum Capacity:** The motherboard supports up to **{max_cap:.0f} GB**, "
                        f"so you can swap out the current sticks for higher-capacity modules."
                    )
                else:
                    answers.append(f"**RAM Assessment:** {topo.get('upgrade_assessment')}")

        # 2. Memory Info (if not combined with topology)
        elif ToolName.GET_MEMORY_INFO.value in data_map:
            mem = data_map[ToolName.GET_MEMORY_INFO.value]
            answers.append(
                f"**Memory (RAM) Status:**\n"
                f"- **Total RAM:** {mem.get('total_gb', 0)} GB\n"
                f"- **Used RAM:** {mem.get('used_gb', 0)} GB ({mem.get('utilization_percent', 0)}%)\n"
                f"- **Available RAM:** {mem.get('available_gb', 0)} GB\n"
                f"- **Swap:** {round(mem.get('swap_total_bytes', 0) / (1024**3), 2)} GB total "
                f"({round(mem.get('swap_used_bytes', 0) / (1024**3), 2)} GB used)"
            )

        # 3. CPU Info
        if ToolName.GET_CPU_INFO.value in data_map:
            cpu = data_map[ToolName.GET_CPU_INFO.value]
            max_freq = f" @ {cpu.get('max_frequency_mhz'):.0f} MHz max" if cpu.get("max_frequency_mhz") else ""
            answers.append(
                f"**Processor (CPU):**\n"
                f"- **Model:** {cpu.get('model')}\n"
                f"- **Architecture:** {cpu.get('architecture')}\n"
                f"- **Physical Cores:** {cpu.get('cores')}\n"
                f"- **Logical Threads:** {cpu.get('threads')}{max_freq}\n"
                f"- **L3 Cache:** {cpu.get('l3_cache') or 'N/A'}"
            )

        # 4. Storage Info
        if ToolName.GET_STORAGE_INFO.value in data_map:
            storage = data_map[ToolName.GET_STORAGE_INFO.value]
            disks = storage.get("devices", [])
            lines = [
                f"**Storage Configuration:** (Total: {storage.get('total_disks')} disk(s) - "
                f"{storage.get('nvme_count')} NVMe, {storage.get('sata_count')} SATA | "
                f"{storage.get('ssd_count')} SSD, {storage.get('hdd_count')} HDD)"
            ]
            for d in disks:
                d_type = "SSD" if d.get("is_ssd") else ("HDD" if d.get("is_ssd") is False else "Disk")
                tran = (d.get("transport") or "unknown").upper()
                model = d.get("model") or "Generic Drive"
                lines.append(f"- **{d.get('name')}**: {d.get('size')} {tran} {d_type} ({model})")
                for p in d.get("children", []):
                    mp = f"mounted on `{p.get('mountpoint')}`" if p.get("mountpoint") else "unmounted"
                    lines.append(f"  - Partition `{p.get('name')}`: {p.get('size')} ({p.get('fstype') or 'raw'}), {mp}")
            answers.append("\n".join(lines))

        # 5. GPU Info
        if ToolName.GET_GPU_INFO.value in data_map:
            gpus = data_map[ToolName.GET_GPU_INFO.value].get("gpus", [])
            if not gpus:
                answers.append("**Graphics (GPU):** No dedicated or integrated GPU detected.")
            else:
                lines = ["**Graphics (GPU):**"]
                for i, g in enumerate(gpus, 1):
                    vram = f"{g.get('vram_mb')} MB VRAM" if g.get("vram_mb") else "Shared System VRAM"
                    driver = f"Driver: {g.get('driver_version')}" if g.get("driver_version") else "Driver: N/A"
                    disc = "Dedicated" if g.get("is_discrete") else "Integrated"
                    lines.append(f"{i}. **{g.get('vendor')} {g.get('model')}** ({disc}) - {vram}, {driver}")
                answers.append("\n".join(lines))

        # 6. Motherboard Info
        if ToolName.GET_MOTHERBOARD_INFO.value in data_map:
            mobo = data_map[ToolName.GET_MOTHERBOARD_INFO.value]
            answers.append(
                f"**Motherboard & BIOS:**\n"
                f"- **Manufacturer:** {mobo.get('manufacturer') or 'Unknown'}\n"
                f"- **Model:** {mobo.get('product_name') or 'Unknown'}\n"
                f"- **BIOS Version:** {mobo.get('bios_version') or 'Unknown'} "
                f"({mobo.get('bios_date') or 'No date'})"
            )

        # 7. System Summary
        if ToolName.GET_SYSTEM_SUMMARY.value in data_map:
            summary = data_map[ToolName.GET_SYSTEM_SUMMARY.value]
            c = summary.get("cpu", {})
            m = summary.get("memory", {})
            st = summary.get("storage", {})
            g_list = summary.get("gpus", [])
            mb = summary.get("motherboard", {})

            gpu_summary_str = (
                ", ".join(f"{g.get('vendor')} {g.get('model')}" for g in g_list)
                if g_list
                else "Integrated Graphics"
            )

            answers.append(
                f"### System Hardware Overview (`{summary.get('hostname')}`)\n\n"
                f"- **OS / Kernel:** {summary.get('os_name')} (Kernel {summary.get('kernel_release')})\n"
                f"- **Motherboard:** {mb.get('manufacturer')} {mb.get('product_name')} (BIOS {mb.get('bios_version')})\n"
                f"- **CPU:** {c.get('model')} ({c.get('cores')} Cores, {c.get('threads')} Threads)\n"
                f"- **Memory:** {m.get('total_gb')} GB RAM ({m.get('utilization_percent')}% used)\n"
                f"- **Storage:** {st.get('total_disks')} drive(s) ({st.get('nvme_count')} NVMe SSD, {st.get('sata_count')} SATA)\n"
                f"- **GPU(s):** {gpu_summary_str}"
            )

        final_content = "\n\n".join(answers) if answers else "Hardware inspection completed, but no details were returned."
        return ProviderResponse(content=final_content, tool_calls=[])
