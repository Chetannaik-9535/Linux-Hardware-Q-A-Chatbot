"""Security package providing allow-listed execution and permission safety."""

from hw_assistant.security.allowlist import ALLOWLISTED_COMMANDS, CommandSpec
from hw_assistant.security.executor import CommandResult, SafeCommandExecutor, default_executor

__all__ = [
    "ALLOWLISTED_COMMANDS",
    "CommandSpec",
    "CommandResult",
    "SafeCommandExecutor",
    "default_executor",
]

