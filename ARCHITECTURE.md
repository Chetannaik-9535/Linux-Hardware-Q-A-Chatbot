# System Architecture & Technical Specifications

## 1. High-Level Architecture Diagram

```
+---------------------------------------------------------------------------------------+
|                                    USER INTERFACES                                    |
|   +--------------------------+  +--------------------------+  +-------------------+   |
|   | Streamlit Web Chat UI    |  | Interactive CLI (Rich)   |  | FastAPI REST API  |   |
|   +--------------------------+  +--------------------------+  +-------------------+   |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             ORCHESTRATION ENGINE & MEMORY                             |
|                                                                                       |
|   +------------------------------------+    +-------------------------------------+   |
|   |     Multi-Turn Session State       |    |       Hardware Fact Cache           |   |
|   |  - Message log (User/Assistant/Tool)    |  - Cached CPU, Memory, Storage specs|   |
|   |  - Tool call traces & timings      |    |  - Fast follow-up reuse             |   |
|   +------------------------------------+    +-------------------------------------+   |
|                                          ^                                            |
|                                          |                                            |
|   +--------------------------------------+----------------------------------------+   |
|   |                     LLM Provider Layer (Dual-Mode)                            |   |
|   |   +--------------------+  +--------------------+  +-----------------------+   |   |
|   |   | Claude 3.5 Sonnet  |  |   Ollama (Local)   |  | Deterministic Mock    |   |   |
|   |   | (Anthropic ToolUse)|  | (Function Calling) |  | (Offline & Testing)   |   |   |
|   |   +--------------------+  +--------------------+  +-----------------------+   |   |
+---------------------------------------------------------------------------------------+
                                           |
                              (Structured Tool Invocation)
                                           v
+---------------------------------------------------------------------------------------+
|                       SAFE TOOL DISPATCHER & ALLOW-LIST FILTER                        |
|                                                                                       |
|   Allowed Tools:                                                                      |
|   - get_cpu_info()             - get_memory_info()        - get_memory_topology()     |
|   - get_storage_info()         - get_gpu_info()           - get_motherboard_info()    |
|   - get_system_summary()                                                              |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                          SAFE COMMAND EXECUTION ENGINE                                |
|                                                                                       |
|   [Security Controls]                                                                 |
|   1. shell=False (Direct execve syscalls, zero subshell spawning)                    |
|   2. Fixed executable paths resolved via shutil.which                                 |
|   3. Fixed, immutable argument vectors (no user-string injection)                     |
|   4. Execution timeout (5.0s default)                                                 |
|   5. Non-interactive sudo (-n flag prevents password hangs)                           |
+---------------------------------------------------------------------------------------+
                      |                                            |
                      v                                            v
     +----------------------------------+        +----------------------------------+
     |   Unprivileged OS Interfaces     |        |    Privileged DMI Interface      |
     |   - lscpu                        |        |    - dmidecode -t memory         |
     |   - free -b                      |        |    - dmidecode -t baseboard,bios |
     |   - lsblk -J (JSON)              |        |                                  |
     |   - lspci -nnmm / lspci -k       |        |   [Privilege Escalation Gate]    |
     |   - nvidia-smi                   |        |   - /etc/sudoers.d/hw-assistant  |
     |   - /sys/class/dmi/id/*          |        |   - Safe report if unauthorized  |
     |   - /proc/cpuinfo, /proc/meminfo |        |                                  |
     +----------------------------------+        +----------------------------------+
                      |                                            |
                      +---------------------+----------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                           PARSING & NORMALIZATION ENGINE                              |
|                                                                                       |
|   - regex & token text parsing        - JSON decoding (lsblk -J)                      |
|   - unit conversion (B -> GB)         - rotational flag SSD vs HDD classification     |
|   - soldered vs socketed RAM analysis - maximum capacity threshold evaluation        |
+---------------------------------------------------------------------------------------+
                                           |
                               (Validated Pydantic JSON)
                                           v
+---------------------------------------------------------------------------------------+
|                         CONTEXTUAL ANSWER SYNTHESIS (LLM)                             |
|                                                                                       |
|   System Prompt Guardrails:                                                           |
|   - Ground answers strictly in verified tool JSON                                     |
|   - Never invent or infer maximum RAM capacity                                        |
|   - Never assume empty slots exist unless verified                                    |
|   - Explicitly report unavailable data or permission limits                           |
+---------------------------------------------------------------------------------------+
```

---

## 2. Security Defense-in-Depth Model

### A. Subprocess Invocation Safety
- **No `shell=True`:** All subprocess commands are executed with `shell=False`. Python passes argument arrays directly to `execve()`, preventing shell metacharacters (`;`, `|`, `&&`, `$()`, `` ` ``) from interpreting or spawning secondary commands.
- **Fixed Command Specifications:** The LLM cannot provide command-line flags. Each tool corresponds to an immutable `CommandSpec` in `ALLOWLISTED_COMMANDS`.
- **Timeouts:** All system invocations are bound to a strict timeout (default: 5.0s) via `subprocess.TimeoutExpired` to prevent hangs caused by misbehaving hardware drivers or deadlocked storage buses.

### B. Root Privilege Handling
Deep hardware topology (`dmidecode`) requires read access to `/dev/mem` or the DMI table, which Linux restricts to `root`. Running the entire assistant or LLM agent as `root` violates the Principle of Least Privilege.

We address this with a 3-tier strategy:
1. **Unprivileged Fallbacks First:** Motherboard specs and BIOS versions are retrieved directly from `/sys/class/dmi/id/*` (world-readable on modern kernels). CPU, memory usage, storage, and GPU inspection require zero elevated permissions (`lscpu`, `free`, `lsblk`, `lspci`).
2. **Narrowly-Scoped Sudoers Rule:** If deep memory topology is needed, a scoped sudoers rule allows running **only** `/usr/sbin/dmidecode` without password prompting:
   ```bash
   <username> ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode
   ```
3. **Non-Interactive Sudo Guard (`-n`):** The executor always passes `-n` to `sudo`. If passwordless sudo is not configured, sudo exits immediately with code 1 instead of hanging on an invisible password prompt. The system catches this and cleanly returns `permission_denied=True` with instructions.

---

## 3. Anti-Hallucination & Grounding Engine

| Scenario | Naive LLM Tendency | Hardware Assistant Enforcement |
|---|---|---|
| User asks: *"Can I upgrade my RAM?"* | Assumes common laptop specs or guesses 32 GB. | Executes `get_memory_topology`. If memory is soldered (LPDDR5 / Row of chips), strictly answers: *"Memory is soldered directly to the motherboard; RAM cannot be upgraded."* |
| Motherboard max capacity is unlisted | Infers max RAM from current RAM (e.g. 16 GB installed -> assumes 32 GB max). | Explicitly states: *"Motherboard maximum capacity is not specified by the BIOS firmware."* |
| Empty RAM slots | Assumes standard 2 slots exist. | Verifies populated vs total devices from DMI Type 16/17. Reports exact empty slot count. |
| GPU VRAM | Guesses standard retail VRAM (e.g. 8 GB for RTX). | Queries `nvidia-smi` or `lspci`. If VRAM is shared or indeterminate, explicitly states *"Shared System VRAM"* or *"Unreported"*. |
| `dmidecode` lacks root | Silently fails or guesses slot count. | Returns structured `permission_denied=True` and instructs the user how to configure `/etc/sudoers.d/hw-assistant`. |

---

## 4. Multi-Turn Conversation & Hardware Caching

To avoid re-running expensive system utilities during follow-up questions, the session state maintains an in-memory `HardwareCache`:
1. **Initial Inquiry:** *"How much RAM do I have?"* -> Triggers `get_memory_info()`, caches RAM metrics.
2. **First Follow-up:** *"What about my CPU?"* -> Retains RAM cache, triggers `get_cpu_info()`, caches CPU metrics.
3. **Second Follow-up:** *"Can I upgrade it?"* -> Recognizes context refers to RAM, pulls cached RAM facts, and triggers `get_memory_topology()` to deliver an authoritative upgrade assessment.
4. **Bypass Flag:** Users can pass `force_refresh=True` via API or UI to invalidate the cache and force fresh hardware queries.

