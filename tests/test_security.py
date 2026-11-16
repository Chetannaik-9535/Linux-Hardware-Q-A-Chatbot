"""Automated tests for security enforcement, allow-lists, and injection prevention."""

import subprocess
from unittest.mock import MagicMock, patch

from hw_assistant.config import settings
from hw_assistant.models.tools import ToolCallRequest
from hw_assistant.orchestration.dispatcher import ToolDispatcher
from hw_assistant.security.allowlist import ALLOWLISTED_COMMANDS
from hw_assistant.security.executor import SafeCommandExecutor


def test_allowlist_contents():
    """Verify standard inspection utilities are in allow-list with fixed args."""
    assert "lscpu" in ALLOWLISTED_COMMANDS
    assert "free" in ALLOWLISTED_COMMANDS
    assert "lsblk" in ALLOWLISTED_COMMANDS
    assert "dmidecode_memory" in ALLOWLISTED_COMMANDS
    assert "lspci" in ALLOWLISTED_COMMANDS
    assert "nvidia_smi" in ALLOWLISTED_COMMANDS

    # Verify no command uses shell=True
    for key, spec in ALLOWLISTED_COMMANDS.items():
        assert isinstance(spec.args, list)
        assert len(spec.args) >= 1
        assert spec.timeout_seconds > 0


def test_reject_unauthorized_command_execution():
    """Ensure arbitrary shell commands cannot be executed."""
    executor = SafeCommandExecutor()

    # Attempt to execute unauthorized commands
    bad_commands = ["rm -rf /", "cat /etc/passwd", "whoami", "curl http://malicious.com", "reboot"]
    for cmd in bad_commands:
        result = executor.execute_command(cmd)
        assert result.exit_code == 126
        assert "Security violation" in result.stderr
        assert result.error is not None


def test_dispatcher_rejects_arbitrary_tool_names():
    """Verify tool dispatcher strictly rejects unknown or injected tool names."""
    dispatcher = ToolDispatcher()

    malicious_calls = [
        ToolCallRequest(id="1", name="get_cpu_info; rm -rf /", arguments={}),
        ToolCallRequest(id="2", name="bash", arguments={}),
        ToolCallRequest(id="3", name="exec", arguments={"cmd": "id"}),
        ToolCallRequest(id="4", name="get_user_passwords", arguments={}),
        ToolCallRequest(id="5", name="get_cpu_info && cat /etc/shadow", arguments={}),
    ]

    for call in malicious_calls:
        res = dispatcher.execute_tool_call(call)
        assert res.success is False
        assert "Security rejection" in (res.error or "")


def test_subprocess_never_uses_shell_true(monkeypatch):
    """Verify that live execution uses shell=False exclusively."""
    monkeypatch.setattr(settings, "hw_mock", "false")

    with patch("subprocess.run") as mock_run, patch("shutil.which", return_value="/usr/bin/lscpu"):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Architecture: x86_64\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        executor = SafeCommandExecutor()
        res = executor.execute_command("lscpu")
        assert res.exit_code == 0

        assert mock_run.called
        kwargs = mock_run.call_args[1]
        # Critical security assertion: shell must be False
        assert kwargs.get("shell") is False
        assert kwargs.get("timeout") == 5.0


def test_subprocess_timeout_handling(monkeypatch):
    """Verify timeout expiration is captured gracefully and does not hang."""
    monkeypatch.setattr(settings, "hw_mock", "false")

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["lscpu"], timeout=5.0)), \
         patch("shutil.which", return_value="/usr/bin/lscpu"):
        executor = SafeCommandExecutor()
        res = executor.execute_command("lscpu")

        assert res.exit_code == 124
        assert "timed out" in res.stderr
        assert res.error is not None


def test_missing_binary_handling(monkeypatch):
    """Verify missing Linux binaries are reported clearly without crashing."""
    monkeypatch.setattr(settings, "hw_mock", "false")

    with patch("shutil.which", return_value=None):
        executor = SafeCommandExecutor()
        res = executor.execute_command("lscpu")

        assert res.binary_not_found is True
        assert res.exit_code == 127
        assert "was not found" in res.stderr

