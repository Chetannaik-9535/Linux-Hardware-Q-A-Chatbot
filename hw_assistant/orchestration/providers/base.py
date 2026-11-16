"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from hw_assistant.models.chat import ChatMessage
from hw_assistant.models.tools import ToolCallRequest, ToolDefinition


class ProviderResponse(BaseModel):
    """Response returned by an LLM provider."""

    content: str | None = Field(None, description="Natural language response text if no tools called or after tool results")
    tool_calls: list[ToolCallRequest] = Field(default_factory=list, description="List of tool calls requested by the model")


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends (Claude, Ollama, Mock)."""

    @abstractmethod
    def generate(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> ProviderResponse:
        """Process messages and return either tool calls or final answer text."""
        raise NotImplementedError

