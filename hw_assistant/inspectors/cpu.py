"""CPU hardware inspector using lscpu and /proc/cpuinfo fallback."""

from __future__ import annotations

from hw_assistant.inspectors.base import BaseInspector
from hw_assistant.models.hardware import CPUInfo


class CPUInspector(BaseInspector):
    """Inspector for processor architecture, cores, threads, and clock rates."""

    def inspect(self) -> CPUInfo:
        """Inspect CPU using lscpu with fallback to /proc/cpuinfo."""
        # 1. Primary: lscpu
        result = self.executor.execute_command("lscpu")
        if result.exit_code == 0 and result.stdout.strip():
            try:
                return self._parse_lscpu(result.stdout)
            except Exception:
                pass  # Fall through to /proc/cpuinfo fallback

        # 2. Fallback: /proc/cpuinfo
        cpuinfo_text, err = self.executor.read_sysfs_or_proc("/proc/cpuinfo")
        if cpuinfo_text and cpuinfo_text.strip():
            return self._parse_proc_cpuinfo(cpuinfo_text)

        # 3. Minimal fallback if neither available
        return CPUInfo(
            vendor="Unknown",
            model="Unknown CPU (utilities unavailable)",
            architecture="Unknown",
            cores=1,
            threads=1,
            raw_source="none",
        )

    def _parse_lscpu(self, stdout: str) -> CPUInfo:
        """Parse structured key-value output from lscpu."""
        data: dict[str, str] = {}
        for line in stdout.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()

        # Vendor and model
        vendor = data.get("Vendor ID", "Unknown")
        model = data.get("Model name", "Unknown Processor")
        arch = data.get("Architecture", "Unknown")

        # Cores and threads calculation
        sockets = int(data.get("Socket(s)", "1"))
        cores_per_socket = int(data.get("Core(s) per socket", "1"))
        physical_cores = sockets * cores_per_socket
        threads = int(data.get("CPU(s)", str(physical_cores)))

        # Frequency values in MHz
        max_freq = self._safe_float(data.get("CPU max MHz"))
        min_freq = self._safe_float(data.get("CPU min MHz"))
        cur_freq = self._safe_float(data.get("CPU MHz"))

        # Caches
        l1d = data.get("L1d cache")
        l1i = data.get("L1i cache")
        l2 = data.get("L2 cache")
        l3 = data.get("L3 cache")

        # Flags
        flags_raw = data.get("Flags", "")
        flags = [f.strip() for f in flags_raw.split() if f.strip()]

        return CPUInfo(
            vendor=vendor,
            model=model,
            architecture=arch,
            cores=physical_cores,
            threads=threads,
            max_frequency_mhz=max_freq,
            min_frequency_mhz=min_freq,
            current_frequency_mhz=cur_freq,
            l1d_cache=l1d,
            l1i_cache=l1i,
            l2_cache=l2,
            l3_cache=l3,
            flags=flags,
            raw_source="lscpu",
        )

    def _parse_proc_cpuinfo(self, text: str) -> CPUInfo:
        """Fallback parser for /proc/cpuinfo."""
        processors = text.split("\n\n")
        threads = 0
        core_ids: set[str] = set()
        model_name = "Unknown CPU"
        vendor = "Unknown"
        cur_freq: float | None = None
        flags: list[str] = []

        for p in processors:
            lines = p.strip().splitlines()
            if not lines:
                continue
            proc_dict: dict[str, str] = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    proc_dict[k.strip()] = v.strip()

            if "processor" in proc_dict:
                threads += 1
            if "core id" in proc_dict and "physical id" in proc_dict:
                core_ids.add(f"{proc_dict['physical id']}:{proc_dict['core id']}")
            elif "core id" in proc_dict:
                core_ids.add(proc_dict["core id"])

            if "model name" in proc_dict and model_name == "Unknown CPU":
                model_name = proc_dict["model name"]
            if "vendor_id" in proc_dict and vendor == "Unknown":
                vendor = proc_dict["vendor_id"]
            if "cpu MHz" in proc_dict and cur_freq is None:
                cur_freq = self._safe_float(proc_dict["cpu MHz"])
            if "flags" in proc_dict and not flags:
                flags = proc_dict["flags"].split()

        cores = len(core_ids) if core_ids else threads

        return CPUInfo(
            vendor=vendor,
            model=model_name,
            architecture="x86_64",  # Default if reading /proc/cpuinfo on Linux PC
            cores=max(cores, 1),
            threads=max(threads, 1),
            current_frequency_mhz=cur_freq,
            flags=flags,
            raw_source="/proc/cpuinfo",
        )

    @staticmethod
    def _safe_float(val: str | None) -> float | None:
        """Safely convert strings to float, returning None on failure."""
        if not val:
            return None
        try:
            return round(float(val), 2)
        except ValueError:
            return None

