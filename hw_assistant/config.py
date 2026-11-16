"""Configuration management for Linux Hardware Q&A Assistant."""

from __future__ import annotations

import platform
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable fallbacks."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings
    llm_provider: Literal["claude", "ollama", "mock"] = "mock"
    anthropic_api_key: str | None = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # Execution & Safety Settings
    execution_timeout_seconds: float = 5.0
    allow_sudo_dmidecode: bool = True

    # Hardware Inspection Environment
    # "auto": automatically use mock if host OS is not Linux, otherwise use live Linux utilities
    # "true": always use mock hardware profiles
    # "false": force live Linux commands (raises error if not on Linux or command missing)
    hw_mock: Literal["auto", "true", "false"] = "auto"
    mock_profile: Literal["thinkpad_x1", "dell_xps", "gaming_desktop", "acer_budget"] = "thinkpad_x1"

    # Server Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501
    log_level: str = "INFO"

    @property
    def is_linux(self) -> bool:
        """Check whether the current runtime OS is native Linux."""
        return platform.system().lower() == "linux"

    @property
    def is_mock_enabled(self) -> bool:
        """Determine whether hardware inspection should run in mock/simulation mode."""
        if self.hw_mock == "true":
            return True
        if self.hw_mock == "false":
            return False
        # "auto" mode: mock if not running on Linux
        return not self.is_linux


settings = Settings()

