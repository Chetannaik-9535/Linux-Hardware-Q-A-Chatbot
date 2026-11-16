"""Anthropic Claude API provider with native tool use."""

from __future__ import annotations

import json
from typing import Any

from hw_assistant.config import settings
from hw_assistant.models.chat import ChatMessage
from hw_assistant.models.tools import ToolCallRequest, ToolDefinition
from hw_assistant.orchestration.providers.base import BaseLLMProvider, ProviderResponse


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider utilizing native tool-calling."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model

        if not self.api_key:
            raise ValueError(
                "Anthropic API key is not configured. Please set ANTHROPIC_API_KEY in your .env file."
            )

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("The 'anthropic' package is required. Install via 'pip install anthropic'.")

    def generate(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str,
    ) -> ProviderResponse:
        """Call Claude with native tool definitions."""
        anthropic_messages = self._format_messages(messages)
        claude_tools = [t.to_claude_tool() for t in tools]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=anthropic_messages,
            tools=claude_tools,
        )

        text_content: list[str] = []
        tool_calls: list[ToolCallRequest] = []

        for block in response.content:
            if getattr(block, "type", "") == "text":
                text_content.append(block.text)
            elif getattr(block, "type", "") == "tool_use":
                tool_calls.append(
                    ToolCallRequest(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        full_text = "\n".join(text_content).strip() if text_content else None
        return ProviderResponse(content=full_text, tool_calls=tool_calls)

    def _format_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Convert internal ChatMessage history to Anthropic API wire format."""
        formatted: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "user":
                formatted.append({"role": "user", "content": msg.content})

            elif msg.role == "assistant":
                blocks: list[dict[str, Any]] = []
                if msg.content:
                    blocks.append({"type": "text", "text": msg.content})
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        blocks.append(
                            {
                                "type": "tool_use",
                                "id": tc["id"],
                                "name": tc["name"],
                                "input": tc.get("arguments", {}),
                            }
                        )
                formatted.append({"role": "assistant", "content": blocks or msg.content or "..."})

            elif msg.role == "tool" and msg.tool_results:
                tool_blocks: list[dict[str, Any]] = []
                for res in msg.tool_results:
                    content_str = (
                        json.dumps(res.data, indent=2)
                        if res.success and res.data is not None
                        else f"Error: {res.error}"
                    )
                    tool_blocks.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": res.tool_call_id,
                            "content": content_str,
                        }
                    )
                formatted.append({"role": "user", "content": tool_blocks})

        return formatted

