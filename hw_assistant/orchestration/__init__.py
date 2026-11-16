"""Orchestration package coordinating tool dispatch, prompts, providers, and conversation memory."""

from hw_assistant.orchestration.dispatcher import ToolDispatcher
from hw_assistant.orchestration.engine import HardwareAssistantEngine, default_engine
from hw_assistant.orchestration.prompts import SYSTEM_PROMPT

__all__ = [
    "HardwareAssistantEngine",
    "default_engine",
    "ToolDispatcher",
    "SYSTEM_PROMPT",
]

