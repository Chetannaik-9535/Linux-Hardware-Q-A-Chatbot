"""Automated tests for LLM tool selection, multi-turn memory, and anti-hallucination."""

from hw_assistant.orchestration.dispatcher import ToolDispatcher
from hw_assistant.orchestration.engine import HardwareAssistantEngine
from hw_assistant.orchestration.providers.mock import MockProvider


def test_tool_selection_ram_query(thinkpad_executor):
    """Test LLM tool selection when user asks about RAM amount."""
    engine = HardwareAssistantEngine(
        provider=MockProvider(),
        dispatcher=ToolDispatcher(thinkpad_executor),
        executor=thinkpad_executor,
    )
    res = engine.ask("How much RAM do I have?")

    assert len(res.tool_traces) >= 1
    assert any(t.tool_name == "get_memory_info" for t in res.tool_traces)
    assert "15.38" in res.message or "15.4" in res.message or "16" in res.message


def test_tool_selection_cpu_query(thinkpad_executor):
    """Test LLM tool selection when user asks about CPU."""
    engine = HardwareAssistantEngine(
        provider=MockProvider(),
        dispatcher=ToolDispatcher(thinkpad_executor),
        executor=thinkpad_executor,
    )
    res = engine.ask("What CPU am I running on?")

    assert len(res.tool_traces) >= 1
    assert any(t.tool_name == "get_cpu_info" for t in res.tool_traces)
    assert "i7-1260P" in res.message
    assert "12" in res.message  # Cores


def test_anti_hallucination_ram_upgrade_soldered(thinkpad_executor):
    """Verify anti-hallucination on ThinkPad X1 with soldered RAM: must NOT claim upgradeable."""
    engine = HardwareAssistantEngine(
        provider=MockProvider(),
        dispatcher=ToolDispatcher(thinkpad_executor),
        executor=thinkpad_executor,
    )
    res = engine.ask("Can I upgrade my RAM?")

    assert len(res.tool_traces) >= 1
    assert any(t.tool_name == "get_memory_topology" for t in res.tool_traces)
    # Anti-hallucination: Must explicitly say cannot upgrade because it is soldered
    assert "cannot upgrade your ram" in res.message.lower()
    assert "soldered" in res.message.lower()


def test_anti_hallucination_ram_upgrade_desktop(desktop_executor):
    """Verify anti-hallucination on Desktop with 2 empty slots: must report exact slots and max."""
    engine = HardwareAssistantEngine(
        provider=MockProvider(),
        dispatcher=ToolDispatcher(desktop_executor),
        executor=desktop_executor,
    )
    res = engine.ask("Can I add more RAM?")

    assert len(res.tool_traces) >= 1
    assert "can upgrade" in res.message.lower()
    assert "2 empty slot" in res.message.lower()
    assert "128" in res.message  # Max motherboard capacity


def test_storage_nvme_vs_sata_query(desktop_executor):
    """Verify storage inquiry correctly identifies NVMe vs SATA."""
    engine = HardwareAssistantEngine(
        provider=MockProvider(),
        dispatcher=ToolDispatcher(desktop_executor),
        executor=desktop_executor,
    )
    res = engine.ask("Is my SSD NVMe or SATA?")

    assert any(t.tool_name == "get_storage_info" for t in res.tool_traces)
    assert "nvme" in res.message.lower()
    assert "sata" in res.message.lower()


def test_multi_turn_conversation_and_caching(thinkpad_executor):
    """Test multi-turn session tracking and caching across follow-ups."""
    engine = HardwareAssistantEngine(
        provider=MockProvider(),
        dispatcher=ToolDispatcher(thinkpad_executor),
        executor=thinkpad_executor,
    )

    # Turn 1: RAM
    res1 = engine.ask("How much RAM do I have?")
    session_id = res1.session_id
    session = engine.sessions[session_id]

    assert session.cache.memory is not None
    assert len(session.messages) == 4  # user, assistant tool_call, tool result, assistant final

    # Turn 2: CPU follow-up
    res2 = engine.ask("What about my CPU?", session_id=session_id)
    assert session.cache.cpu is not None
    assert "i7-1260P" in res2.message

    # Turn 3: RAM upgrade follow-up
    res3 = engine.ask("Can I upgrade it?", session_id=session_id)
    assert "cannot upgrade" in res3.message.lower()
