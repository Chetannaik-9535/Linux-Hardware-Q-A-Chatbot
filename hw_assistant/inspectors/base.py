"""Base class for all hardware inspectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pydantic import BaseModel

from hw_assistant.security.executor import SafeCommandExecutor, default_executor


class BaseInspector(ABC):
    """Abstract base inspector interface."""

    def __init__(self, executor: SafeCommandExecutor | None = None) -> None:
        self.executor = executor or default_executor

    @abstractmethod
    def inspect(self) -> BaseModel:
        """Execute safe inspection and return a validated Pydantic model."""
        raise NotImplementedError

