"""Core orchestration engine managing tool calling, conversation memory, and hardware caching."""

from __future__ import annotations

import time
import uuid

from hw_assistant.config import settings
from hw_assistant.models.chat import (
    ChatMessage,
    ChatResponse,
    ChatSession,
)
from hw_assistant.models.tools import (
    HARDWARE_TOOLS,
    ToolExecutionResult,
)
from hw_assistant.orchestration.dispatcher import ToolDispatcher
from hw_assistant.orchestration.prompts import SYSTEM_PROMPT
from hw_assistant.orchestration.providers.base import BaseLLMProvider
from hw_assistant.orchestration.providers.claude import ClaudeProvider
from hw_assistant.orchestration.providers.mock import MockProvider
from hw_assistant.orchestration.providers.ollama import OllamaProvider
from hw_assistant.security.executor import SafeCommandExecutor, default_executor


class HardwareAssistantEngine:
    """Main orchestration engine coordinating conversation memory, tool calling, and safe execution."""

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        dispatcher: ToolDispatcher | None = None,
        executor: SafeCommandExecutor | None = None,
    ) -> None:
        self.executor = executor or default_executor
        self.dispatcher = dispatcher or ToolDispatcher(self.executor)
        self.sessions: dict[str, ChatSession] = {}

        # Resolve LLM Provider
        if provider:
            self.provider = provider
        else:
            self.provider = self._resolve_provider()

    def _resolve_provider(self) -> BaseLLMProvider:
        """Instantiate configured LLM provider based on settings."""
        p_type = settings.llm_provider.lower()
        if p_type == "claude":
            try:
                return ClaudeProvider()
            except Exception as e:
                # Log and fallback to MockProvider
                print(f"[Warning] Failed to initialize Claude provider ({e}). Falling back to Mock.")
                return MockProvider()
        elif p_type == "ollama":
            return OllamaProvider()
        else:
            return MockProvider()

    def get_or_create_session(self, session_id: str | None = None) -> ChatSession:
        """Retrieve existing multi-turn chat session or initialize a new one."""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        new_id = session_id or str(uuid.uuid4())
        session = ChatSession(session_id=new_id)
        self.sessions[new_id] = session
        return session

    def reset_session(self, session_id: str) -> None:
        """Clear conversation history and hardware cache for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def ask(
        self,
        query: str,
        session_id: str | None = None,
        force_refresh: bool = False,
    ) -> ChatResponse:
        """Process a user question through intent resolution, safe tool execution, and grounded answer synthesis.

        Args:
            query: User's question in natural language.
            session_id: Optional ID for continuing an existing conversation.
            force_refresh: If True, invalidates hardware cache before execution.

        Returns:
            ChatResponse containing the verified answer, tool traces, and metadata.
        """
        start_time = time.perf_counter()
        session = self.get_or_create_session(session_id)

        if force_refresh:
            session.cache.clear()

        # Append user query to session
        session.add_user_message(query)

        all_tool_traces: list[ToolExecutionResult] = []
        cached_used: list[str] = []

        max_turns = 5
        turn_count = 0
        final_answer = ""

        # Construct context-rich system prompt with cached hardware state if present
        augmented_prompt = self._build_prompt_with_cache(session)

        while turn_count < max_turns:
            turn_count += 1

            # Call LLM Provider
            response = self.provider.generate(
                messages=session.messages,
                tools=HARDWARE_TOOLS,
                system_prompt=augmented_prompt,
            )

            # Case A: LLM requested one or more tool calls
            if response.tool_calls:
                turn_results: list[ToolExecutionResult] = []

                # Execute requested allow-listed tools
                for tc in response.tool_calls:
                    exec_result = self.dispatcher.execute_tool_call(tc)
                    turn_results.append(exec_result)
                    all_tool_traces.append(exec_result)

                    # Update hardware cache with fresh data
                    if exec_result.success and exec_result.data:
                        cache_key = exec_result.tool_name.replace("get_", "").replace("_info", "")
                        session.cache.set(cache_key, exec_result.data)

                # Record turn in session memory
                session.add_assistant_message(
                    text=response.content or "",
                    tool_calls=[{"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in response.tool_calls],
                )
                session.messages.append(
                    ChatMessage(
                        role="tool",
                        content="Tool execution results",
                        tool_results=turn_results,
                    )
                )

            # Case B: LLM returned final synthesized text answer
            elif response.content:
                final_answer = response.content
                session.add_assistant_message(text=final_answer, tool_results=all_tool_traces)
                break

            else:
                final_answer = "Hardware inspection completed, but no further details could be retrieved."
                session.add_assistant_message(text=final_answer)
                break

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return ChatResponse(
            session_id=session.session_id,
            message=final_answer,
            tool_traces=all_tool_traces,
            cached_data_used=cached_used,
            provider=self.provider.__class__.__name__,
            execution_time_ms=round(duration_ms, 2),
        )

    def _build_prompt_with_cache(self, session: ChatSession) -> str:
        """Inject verified cached hardware summaries into prompt to prevent redundant tool calls on follow-ups."""
        cached_sections: list[str] = []
        if session.cache.cpu:
            c = session.cache.cpu
            cached_sections.append(f"- Previously verified CPU: {c.get('model')}, {c.get('cores')} cores/{c.get('threads')} threads")
        if session.cache.memory:
            m = session.cache.memory
            cached_sections.append(f"- Previously verified RAM: {m.get('total_gb')} GB total ({m.get('available_gb')} GB available)")
        if session.cache.storage:
            s = session.cache.storage
            cached_sections.append(f"- Previously verified Storage: {s.get('total_disks')} disk(s) ({s.get('nvme_count')} NVMe)")

        if cached_sections:
            return (
                f"{SYSTEM_PROMPT}\n\n"
                f"CURRENT SESSION CACHED HARDWARE FACTS:\n"
                + "\n".join(cached_sections)
                + "\nYou may reuse these facts for follow-up questions or re-invoke tools if the user requests updated data."
            )
        return SYSTEM_PROMPT


# Default engine instance
default_engine = HardwareAssistantEngine()

