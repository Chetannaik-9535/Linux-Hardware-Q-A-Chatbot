"""Ollama local LLM provider with native tool-calling."""

from __future__ import annotations

import json
import uuid
from typing import Any
import httpx

from hw_assistant.config import settings
from hw_assistant.models.chat import ChatMessage
from hw_assistant.models.tools import ToolCallRequest, ToolDefinition
from hw_assistant.orchestration.providers.base import BaseLLMProvider, ProviderResponse


class OllamaProvider(BaseLLMProvider):
    """Local Ollama provider with function-calling support for complete offline privacy."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    def generate(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> ProviderResponse:
        """Call Ollama chat endpoint with function definitions."""
        ollama_messages = [{"role": "system", "content": system_prompt}]
        ollama_messages.extend(self._format_messages(messages))

        ollama_tools = [t.to_ollama_tool() for t in tools]

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
        }
        if ollama_tools:
            payload["tools"] = ollama_tools

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code != 200:
                    raise RuntimeError(
                        f"Ollama API returned HTTP {res.status_code}: {res.text}. "
                        "Ensure the Ollama service is running and the model is pulled."
                    )
                data = res.json()
        except httpx.ConnectError:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.base_url}. "
                "Please verify that Ollama is installed and running (`ollama serve`)."
            )

        msg_obj = data.get("message", {})
        content = msg_obj.get("content") or None
        tool_calls_raw = msg_obj.get("tool_calls", [])

        tool_calls: list[ToolCallRequest] = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            name = func.get("name", "")
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(
                ToolCallRequest(
                    id=str(uuid.uuid4())[:8],
                    name=name,
                    arguments=args,
                )
            )

        return ProviderResponse(content=content, tool_calls=tool_calls)

    def _format_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Format chat messages for Ollama API."""
        formatted: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "user":
                formatted.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                m: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
                if msg.tool_calls:
                    m["tool_calls"] = [
                        {
                            "function": {
                                "name": tc["name"],
                                "arguments": tc.get("arguments", {}),
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                formatted.append(m)
            elif msg.role == "tool" and msg.tool_results:
                for res in msg.tool_results:
                    content_str = (
                        json.dumps(res.data)
                        if res.success and res.data is not None
                        else f"Error: {res.error}"
                    )
                    formatted.append(
                        {
                            "role": "tool",
                            "content": content_str,
                            "name": res.tool_name,
                        }
                    )

        return formatted

