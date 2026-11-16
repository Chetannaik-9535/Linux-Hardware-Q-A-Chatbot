"""Models for multi-turn chat sessions, message state, and API communication."""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal
from pydantic import BaseModel, Field
from hw_assistant.models.tools import ToolExecutionResult


class ChatMessage(BaseModel):
    """A single turn in the hardware assistant conversation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_results: list[ToolExecutionResult] | None = None
    created_at: float = Field(default_factory=time.time)


class HardwareCache(BaseModel):
    """Locally cached hardware facts to avoid re-running unchanged commands on follow-ups."""

    cpu: dict[str, Any] | None = None
    memory: dict[str, Any] | None = None
    memory_topology: dict[str, Any] | None = None
    storage: dict[str, Any] | None = None
    gpu: dict[str, Any] | None = None
    motherboard: dict[str, Any] | None = None
    system_summary: dict[str, Any] | None = None
    last_updated: float = Field(default_factory=time.time)

    def get(self, key: str) -> dict[str, Any] | None:
        """Fetch cached component dictionary if present."""
        return getattr(self, key, None)

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Store component data in cache and update timestamp."""
        if hasattr(self, key):
            setattr(self, key, value)
            self.last_updated = time.time()

    def clear(self) -> None:
        """Invalidate all cached hardware facts."""
        self.cpu = None
        self.memory = None
        self.memory_topology = None
        self.storage = None
        self.gpu = None
        self.motherboard = None
        self.system_summary = None
        self.last_updated = time.time()


class ChatSession(BaseModel):
    """Full session state including conversation history and hardware cache."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[ChatMessage] = Field(default_factory=list)
    cache: HardwareCache = Field(default_factory=HardwareCache)
    created_at: float = Field(default_factory=time.time)

    def add_user_message(self, text: str) -> ChatMessage:
        """Append user question to message log."""
        msg = ChatMessage(role="user", content=text)
        self.messages.append(msg)
        return msg

    def add_assistant_message(
        self,
        text: str,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_results: list[ToolExecutionResult] | None = None,
    ) -> ChatMessage:
        """Append assistant response and tool traces to message log."""
        msg = ChatMessage(
            role="assistant",
            content=text,
            tool_calls=tool_calls,
            tool_results=tool_results,
        )
        self.messages.append(msg)
        return msg


class ChatRequest(BaseModel):
    """Payload for API chat endpoint."""

    message: str = Field(..., description="User question in natural language")
    session_id: str | None = Field(None, description="Optional existing session ID for multi-turn context")
    force_refresh: bool = Field(False, description="Whether to bypass hardware cache and re-query tools")


class ChatResponse(BaseModel):
    """Response returned by the hardware assistant."""

    session_id: str
    message: str
    tool_traces: list[ToolExecutionResult] = Field(default_factory=list)
    cached_data_used: list[str] = Field(default_factory=list)
    provider: str
    execution_time_ms: float = 0.0

