"""Pytest test configuration and fixtures."""

import pytest
from hw_assistant.config import settings
from hw_assistant.security.executor import SafeCommandExecutor


@pytest.fixture(autouse=True)
def force_mock_mode(monkeypatch):
    """Ensure all tests run with mock execution enabled by default."""
    monkeypatch.setattr(settings, "hw_mock", "true")


@pytest.fixture
def thinkpad_executor():
    """Executor pinned to the ThinkPad X1 Carbon mock profile."""
    return SafeCommandExecutor(mock_profile="thinkpad_x1")


@pytest.fixture
def dell_executor():
    """Executor pinned to the Dell XPS 15 mock profile."""
    return SafeCommandExecutor(mock_profile="dell_xps")


@pytest.fixture
def desktop_executor():
    """Executor pinned to the AMD Gaming Desktop mock profile."""
    return SafeCommandExecutor(mock_profile="gaming_desktop")


@pytest.fixture
def budget_executor():
    """Executor pinned to the Acer Budget Laptop mock profile."""
    return SafeCommandExecutor(mock_profile="acer_budget")

