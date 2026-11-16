"""Safe subprocess and filesystem inspection execution engine."""

from __future__ import annotations

import os
import subprocess
import time
from typing import NamedTuple

from hw_assistant.config import settings
from hw_assistant.mock_data.profiles import PROFILES
from hw_assistant.security.allowlist import (
    ALLOWLISTED_COMMANDS,
    CommandSpec,
    resolve_binary_path,
)


class CommandResult(NamedTuple):
    """Execution output container."""

    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    permission_denied: bool = False
    binary_not_found: bool = False
    error: str | None = None
    command_executed: list[str] | None = None


class SafeCommandExecutor:
    """Safe execution engine that enforces allow-listing, shell=False, and timeout limits."""

    def __init__(self, mock_profile: str | None = None) -> None:
        self.mock_profile = mock_profile or settings.mock_profile

    def execute_command(self, cmd_key: str) -> CommandResult:
        """Safely execute an allow-listed command or retrieve its simulated output.

        Args:
            cmd_key: Key in ALLOWLISTED_COMMANDS (e.g. 'lscpu', 'lsblk', 'free').

        Returns:
            CommandResult containing stdout, stderr, exit_code, and safety flags.
        """
        # 1. ALLOW-LIST ENFORCEMENT
        if cmd_key not in ALLOWLISTED_COMMANDS:
            return CommandResult(
                stdout="",
                stderr=f"Security violation: Command '{cmd_key}' is not in the allow-list.",
                exit_code=126,
                duration_ms=0.0,
                error=f"Command '{cmd_key}' rejected by security policy.",
            )

        spec: CommandSpec = ALLOWLISTED_COMMANDS[cmd_key]

        # 2. SIMULATION / MOCK MODE CHECK
        if settings.is_mock_enabled:
            return self._execute_mock(cmd_key)

        # 3. REAL LINUX EXECUTION
        start_time = time.perf_counter()

        # Locate binary securely
        binary_path = resolve_binary_path(spec.binary_name, spec.preferred_path)
        if not binary_path:
            return CommandResult(
                stdout="",
                stderr=f"Utility '{spec.binary_name}' was not found on system PATH.",
                exit_code=127,
                duration_ms=0.0,
                binary_not_found=True,
                error=f"Linux utility '{spec.binary_name}' is not installed.",
            )

        # Build argument vector (fixed arguments, no shell strings)
        argv = [binary_path] + spec.args[1:]

        # Handle root requirements (e.g., dmidecode)
        is_root = False
        try:
            is_root = (os.geteuid() == 0)  # type: ignore[attr-defined]
        except AttributeError:
            is_root = False

        if spec.requires_root and not is_root:
            if settings.allow_sudo_dmidecode:
                sudo_bin = resolve_binary_path("sudo")
                if sudo_bin:
                    # '-n' (non-interactive): Prevents sudo from blocking for password input
                    argv = [sudo_bin, "-n"] + argv
                else:
                    return CommandResult(
                        stdout="",
                        stderr="Command requires root privileges and 'sudo' is not available.",
                        exit_code=1,
                        duration_ms=0.0,
                        permission_denied=True,
                        error="Elevated permissions required but sudo is missing.",
                    )
            else:
                return CommandResult(
                    stdout="",
                    stderr="Command requires root privileges and allow_sudo_dmidecode is disabled.",
                    exit_code=1,
                    duration_ms=0.0,
                    permission_denied=True,
                    error="Elevated permissions required.",
                )

        # 4. EXECUTE SUBPROCESS
        try:
            # shell=False: CRITICAL security barrier preventing command injection
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                shell=False,
                timeout=spec.timeout_seconds,
                check=False,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Inspect stderr for permission denials
            perm_denied = False
            err_msg = None
            if proc.returncode != 0:
                err_lower = proc.stderr.lower()
                if (
                    "password is required" in err_lower
                    or "permission denied" in err_lower
                    or "operation not permitted" in err_lower
                    or "no /dev/mem" in err_lower
                ):
                    perm_denied = True
                    err_msg = (
                        f"Permission denied executing '{spec.binary_name}'. "
                        "Elevated read permissions (/dev/mem or DMI table) are required."
                    )
                else:
                    err_msg = proc.stderr.strip() or f"Process exited with code {proc.returncode}"

            return CommandResult(
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                duration_ms=round(duration_ms, 2),
                permission_denied=perm_denied,
                error=err_msg,
                command_executed=argv,
            )

        except subprocess.TimeoutExpired:
            return CommandResult(
                stdout="",
                stderr=f"Command '{spec.binary_name}' timed out after {spec.timeout_seconds}s.",
                exit_code=124,
                duration_ms=spec.timeout_seconds * 1000.0,
                error=f"Timeout of {spec.timeout_seconds}s exceeded.",
                command_executed=argv,
            )
        except PermissionError as e:
            return CommandResult(
                stdout="",
                stderr=str(e),
                exit_code=126,
                duration_ms=0.0,
                permission_denied=True,
                error=f"OS PermissionError: {e}",
                command_executed=argv,
            )
        except Exception as e:
            return CommandResult(
                stdout="",
                stderr=str(e),
                exit_code=1,
                duration_ms=0.0,
                error=f"Unexpected execution error: {e}",
                command_executed=argv,
            )

    def read_sysfs_or_proc(self, path: str) -> tuple[str | None, str | None]:
        """Safely read unprivileged pseudo-filesystem paths (/proc, /sys).

        Args:
            path: Target path (e.g., '/proc/meminfo', '/sys/class/dmi/id/product_name').

        Returns:
            Tuple of (content_string, error_string).
        """
        if settings.is_mock_enabled:
            profile = PROFILES.get(self.mock_profile, PROFILES["thinkpad_x1"])
            if path in profile:
                return profile[path], None
            # Check /sys/class/dmi/id dictionary
            if path.startswith("/sys/class/dmi/id/"):
                field = path.split("/")[-1]
                dmi_data = profile.get("/sys/class/dmi/id", {})
                if isinstance(dmi_data, dict) and field in dmi_data:
                    return dmi_data[field], None
            return None, f"Mock path '{path}' not found."

        # Real Linux file read
        if not os.path.exists(path):
            return None, f"Path '{path}' does not exist on this machine."

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(), None
        except PermissionError:
            return None, f"Permission denied reading '{path}'."
        except Exception as e:
            return None, f"Failed reading '{path}': {e}"

    def _execute_mock(self, cmd_key: str) -> CommandResult:
        """Return deterministic simulated output for the active mock profile."""
        start = time.perf_counter()
        profile = PROFILES.get(self.mock_profile, PROFILES["thinkpad_x1"])
        output = profile.get(cmd_key, "")

        duration_ms = (time.perf_counter() - start) * 1000.0
        return CommandResult(
            stdout=output,
            stderr="",
            exit_code=0,
            duration_ms=round(duration_ms, 2),
            command_executed=[f"(mock) {cmd_key}"],
        )


# Global default executor instance
default_executor = SafeCommandExecutor()

