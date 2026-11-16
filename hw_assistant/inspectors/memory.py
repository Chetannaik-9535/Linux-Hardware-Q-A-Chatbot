"""Memory usage inspector using free -b and /proc/meminfo fallback."""

from __future__ import annotations

from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.models.hardware import MemoryInfo


class MemoryInspector(BaseInspector):
    """Inspector for volatile RAM metrics, allocations, buffers, and swap."""

    def inspect(self) -> MemoryInfo:
        """Inspect RAM metrics using free -b with /proc/meminfo fallback."""
        # 1. Primary: free -b
        result = self.executor.execute_command("free")
        if result.exit_code == 0 and result.stdout.strip():
            try:
                return self._parse_free(result.stdout)
            except Exception:
                pass

        # 2. Fallback: /proc/meminfo
        meminfo_text, err = self.executor.read_sysfs_or_proc("/proc/meminfo")
        if meminfo_text and meminfo_text.strip():
            return self._parse_proc_meminfo(meminfo_text)

        # 3. Minimal fallback
        return MemoryInfo(
            total_bytes=0,
            used_bytes=0,
            available_bytes=0,
            free_bytes=0,
            raw_source="none",
        )

    def _parse_free(self, stdout: str) -> MemoryInfo:
        """Parse raw stdout from 'free -b'."""
        lines = [line.split() for line in stdout.strip().splitlines() if line.strip()]

        total = 0
        used = 0
        free = 0
        cached = 0
        avail = 0
        swap_total = 0
        swap_used = 0
        swap_free = 0

        for parts in lines:
            if not parts:
                continue
            header = parts[0].lower().rstrip(":")
            if header == "mem":
                # Header format: [Mem:, total, used, free, (shared), buff/cache, available]
                total = int(parts[1])
                used = int(parts[2])
                free = int(parts[3])
                if len(parts) >= 6:
                    cached = int(parts[5])
                if len(parts) >= 7:
                    avail = int(parts[6])
                else:
                    avail = free + cached
            elif header == "swap":
                swap_total = int(parts[1])
                swap_used = int(parts[2])
                swap_free = int(parts[3])

        return MemoryInfo(
            total_bytes=total,
            used_bytes=used,
            available_bytes=avail,
            free_bytes=free,
            cached_bytes=cached,
            swap_total_bytes=swap_total,
            swap_used_bytes=swap_used,
            swap_free_bytes=swap_free,
            raw_source="free",
        )

    def _parse_proc_meminfo(self, text: str) -> MemoryInfo:
        """Parse structured key-value lines from /proc/meminfo."""
        metrics: dict[str, int] = {}
        for line in text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                num = "".join(ch for ch in v if ch.isdigit())
                if num:
                    metrics[k.strip()] = int(num) * 1024  # Convert kB to bytes

        total = metrics.get("MemTotal", 0)
        free = metrics.get("MemFree", 0)
        avail = metrics.get("MemAvailable", free)
        buffers = metrics.get("Buffers", 0)
        cached = metrics.get("Cached", 0)
        used = max(0, total - avail)

        swap_total = metrics.get("SwapTotal", 0)
        swap_free = metrics.get("SwapFree", 0)
        swap_used = max(0, swap_total - swap_free)

        return MemoryInfo(
            total_bytes=total,
            used_bytes=used,
            available_bytes=avail,
            free_bytes=free,
            cached_bytes=buffers + cached,
            swap_total_bytes=swap_total,
            swap_used_bytes=swap_used,
            swap_free_bytes=swap_free,
            raw_source="/proc/meminfo",
        )

