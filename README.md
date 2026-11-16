# Local Linux Hardware AI Assistant 💻🤖

An interview-grade, production-quality AI chatbot that runs on a Linux laptop and answers natural-language questions about the actual hardware installed on the machine.

The assistant directly inspects system hardware using native Linux utilities (`lscpu`, `free`, `lsblk`, `lspci`, `dmidecode`, `nvidia-smi`, `/proc/`, `/sys/`), converts raw outputs into validated Pydantic JSON schemas, and synthesizes accurate, strictly grounded responses via **native LLM tool-calling**.

> **Zero Hallucination Guarantee:** The assistant never invents hardware specs, never assumes empty slots exist, never infers motherboard capacity from installed RAM, and explicitly reports when data or permissions are unavailable.

---

## 📑 Table of Contents

- [Core Architecture & Pipeline](#-core-architecture--pipeline)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation & Quickstart](#-installation--quickstart)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [How to Run the Application](#-how-to-run-the-application)
  - [1. Streamlit Web Chat Interface](#1-streamlit-web-chat-interface)
  - [2. Interactive CLI](#2-interactive-cli)
  - [3. FastAPI REST Backend](#3-fastapi-rest-backend)
- [Security & Safe Command Execution](#-security--safe-command-execution)
- [Root Permission Handling & Scoped Sudoers](#-root-permission-handling--scoped-sudoers)
- [Privacy: Cloud vs. Local Inference](#-privacy-cloud-vs-local-inference)
- [Testing & Verification](#-testing--verification)
- [Known Limitations](#-known-limitations)

---

## 🏗️ Core Architecture & Pipeline

```
User Natural Language Question
             │
             ▼
   LLM Intent Understanding (Claude / Ollama / Mock)
             │
             ▼
       Tool Selection (get_cpu_info, get_memory_topology, etc.)
             │
             ▼
   Safe Tool Execution Engine
    - Allow-list verification
    - shell=False (execve syscall)
    - Fixed executable paths & immutable arguments
    - 5.0s execution timeout
             │
             ▼
   Linux Hardware Inspection
    (lscpu, free -b, lsblk -J, dmidecode, lspci, /proc, /sys)
             │
             ▼
   Output Parsing & Normalization
    (Regex, JSON decoding, unit conversions)
             │
             ▼
   Structured Pydantic JSON Schemas
             │
             ▼
   Contextual Answer Synthesis (Strict Anti-Hallucination)
             │
             ▼
   User Response + Collapsible Tool Execution Traces
```

---

## ✨ Key Features

1. **Deterministic Tool-Calling:** The LLM cannot execute arbitrary bash commands. It selects from an immutable allow-list of predefined functions.
2. **Deep RAM Upgrade Analysis:** Inspects physical slots, module form factors, speeds, and max motherboard limits (`dmidecode -t memory`). Correctly identifies soldered LPDDR RAM vs socketed SODIMMs.
3. **Storage Bus & Media Classification:** Parses `lsblk -J` to distinguish NVMe vs SATA transports and SSDs (`rota=0`) vs HDDs (`rota=1`).
4. **Dual GPU Detection:** Identifies both integrated graphics (Intel Iris Xe, AMD Vega) and discrete GPUs (NVIDIA GeForce/RTX via `nvidia-smi` with VRAM metrics).
5. **Multi-Turn Conversation Memory:** Maintains chat context and an in-memory **Hardware Fact Cache** so follow-up inquiries (e.g. *"What about my CPU?"*, *"Can I upgrade it?"*) do not trigger redundant system scans.
6. **Cross-Platform Mock & Simulation Mode:** Built-in simulation mode (`hw_mock=auto`) enables running the full test suite, UI, and CLI on Windows/macOS or CI pipelines using realistic Linux hardware profiles (ThinkPad X1, Dell XPS 15, Desktop PC, Acer Laptop). Native Linux machines use real OS commands.
7. **Privacy Modes:** Full support for local offline inference via **Ollama**, cloud-based inference via **Claude 3.5 Sonnet**, and offline deterministic mock evaluation.

---

## 🛠️ Technology Stack

| Layer | Component | Purpose |
|---|---|---|
| **Language** | Python 3.11+ (Tested on Python 3.13) | Core runtime |
| **Data Validation** | Pydantic v2 & Pydantic Settings | Strict schema validation, unit conversions, and settings |
| **Execution Safety** | Python `subprocess` with `shell=False` | Safe OS inspection with timeouts and allow-list |
| **Web UI** | Streamlit 1.33+ | Modern web chat with hardware cards & tool execution traces |
| **API Backend** | FastAPI & Uvicorn | Production-ready REST endpoints |
| **Terminal CLI** | Rich & Argparse | Interactive colored REPL with Markdown and telemetry tables |
| **LLM Cloud** | Anthropic Claude API (`anthropic`) | High-precision native tool calling (`tool_use`) |
| **LLM Local** | Ollama (`httpx` / `ollama`) | 100% private on-device local execution |
| **Testing** | Pytest & FastAPI TestClient | 26 automated unit and security tests |

---

## 📁 Project Structure

```
linux-hardware-assistant/
├── hw_assistant/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings & environment detection
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py                # FastAPI REST endpoints
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py               # Interactive Rich CLI application
│   ├── ui/
│   │   ├── __init__.py
│   │   └── streamlit_app.py      # Streamlit web chat UI
│   ├── security/
│   │   ├── __init__.py
│   │   ├── allowlist.py          # Fixed command specs & binary resolution
│   │   └── executor.py           # Subprocess runner (shell=False, non-root guards)
│   ├── inspectors/
│   │   ├── __init__.py
│   │   ├── base.py               # BaseInspector abstract class
│   │   ├── cpu.py                # lscpu & /proc/cpuinfo parser
│   │   ├── memory.py             # free -b & /proc/meminfo parser
│   │   ├── memory_topology.py    # dmidecode -t memory & upgrade logic
│   │   ├── storage.py            # lsblk -J (NVMe/SATA, SSD/HDD) parser
│   │   ├── gpu.py                # lspci -nnmm & nvidia-smi parser
│   │   ├── motherboard.py        # /sys/class/dmi/id & dmidecode baseboard parser
│   │   └── system.py             # SystemSummary aggregator
│   ├── mock_data/
│   │   ├── __init__.py
│   │   └── profiles.py           # Virtual Linux hardware profiles
│   ├── models/
│   │   ├── __init__.py
│   │   ├── hardware.py           # Pydantic schemas for hardware metrics
│   │   ├── tools.py              # Tool definitions, calls, and execution results
│   │   └── chat.py               # Message state, session memory, hardware cache
│   └── orchestration/
│       ├── __init__.py
│       ├── dispatcher.py         # Routes tool calls to inspectors
│       ├── prompts.py            # Anti-hallucination system prompt
│       ├── engine.py             # Core tool loop, caching & multi-turn memory
│       └── providers/
│           ├── __init__.py
│           ├── base.py           # BaseLLMProvider interface
│           ├── claude.py         # Anthropic Claude 3.5 Sonnet provider
│           ├── ollama.py         # Local Ollama provider
│           └── mock.py           # Deterministic simulator for tests/demos
├── scripts/
│   └── setup_sudoers.sh          # Narrowly scoped sudoers configuration
├── tests/
│   ├── conftest.py               # Test fixtures and mock overrides
│   ├── test_security.py          # Allow-list, injection rejection, timeouts
│   ├── test_parsers.py           # lscpu, free, lsblk, dmidecode, lspci tests
│   ├── test_orchestration.py     # Tool selection, follow-ups, anti-hallucination
│   └── test_api.py               # FastAPI testclient endpoints
├── .env.example                  # Environment configuration template
├── pyproject.toml                # Project metadata and dependencies
├── requirements.txt              # Pip requirements
├── ARCHITECTURE.md               # Detailed technical specifications
└── README.md                     # Documentation
```

---

## 🚀 Installation & Quickstart

### Prerequisites
- Python 3.11+
- Linux host (Ubuntu, Debian, Fedora, Arch) for live hardware queries, or Windows/macOS for simulated profile mode.

### 1. Clone & Set Up Virtual Environment

```bash
cd "Linux hardware Q&A Chatbot"
python3 -m venv venv
source venv/bin/activate    # On Windows: .\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration & Environment Variables

Copy the example environment configuration:

```bash
cp .env.example .env
```

Edit `.env` according to your preferred LLM provider:

```ini
# LLM Provider: "mock", "claude", or "ollama"
LLM_PROVIDER=mock

# Anthropic Claude API (If LLM_PROVIDER=claude)
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Ollama Local LLM (If LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Execution Settings
EXECUTION_TIMEOUT_SECONDS=5.0
ALLOW_SUDO_DMIDECODE=true

# Mock Mode Settings ("auto", "true", or "false")
HW_MOCK=auto
MOCK_PROFILE=thinkpad_x1
```

---

## 🖥️ How to Run the Application

### 1. Streamlit Web Chat Interface

Launch the interactive web UI:

```bash
streamlit run hw_assistant/ui/streamlit_app.py
```

- Open `http://localhost:8501` in your browser.
- Displays live hardware telemetry cards (CPU, RAM, Disks, GPU).
- Interactive chat conversation with expandable **Tool Execution Traces** showing exact execution timings and JSON payloads.
- Includes quick-inquiry buttons and a hardware profile switcher.

### 2. Interactive CLI

Run the Rich-powered command-line interface:

```bash
# Launch interactive chat REPL
python -m hw_assistant.cli.main

# Single-shot query
python -m hw_assistant.cli.main --query "Can I upgrade my RAM?"

# Display system summary table
python -m hw_assistant.cli.main --summary

# Test with a specific virtual profile
python -m hw_assistant.cli.main --query "Is my SSD NVMe or SATA?" --profile gaming_desktop
```

### 3. FastAPI REST Backend

Start the API server:

```bash
uvicorn hw_assistant.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI Swagger documentation is available at `http://localhost:8000/docs`.

#### Example API Call:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How much RAM do I have?"}'
```

---

## 🔒 Security & Safe Command Execution

To prevent Arbitrary Code Execution (ACE) and Command Injection vulnerabilities, the assistant enforces strict security boundaries:

1. **No `shell=True`:** Commands are invoked directly via OS syscalls (`execve`) through `subprocess.run(shell=False)`.
2. **Fixed Command Allow-List:** The LLM cannot specify bash strings or arguments. Tool calls are strictly mapped to fixed `CommandSpec` definitions:
   - `get_cpu_info` ➔ `["/usr/bin/lscpu"]`
   - `get_memory_info` ➔ `["/usr/bin/free", "-b"]`
   - `get_storage_info` ➔ `["/usr/bin/lsblk", "-J", "-o", "..."]`
   - `get_gpu_info` ➔ `["/usr/bin/lspci", "-nnmm"]`
   - `get_memory_topology` ➔ `["/usr/sbin/dmidecode", "-t", "memory"]`
3. **Execution Timeouts:** Every command is wrapped in a 5.0-second timeout to prevent deadlocks.
4. **Injection Rejection:** Tool names containing shell metacharacters (`;`, `&&`, `|`, `$(...)`) are rejected immediately by `ToolDispatcher` with a security audit event.

---

## 🔑 Root Privilege Handling & Scoped Sudoers

Deep physical RAM topology inspection (`dmidecode`) requires elevated permissions to read `/dev/mem` or `/sys/firmware/dmi/tables`.

**Security Rule:** Never run the entire AI assistant or web server as `root`.

### Least-Privilege Setup:
Run the provided automated script to install a scoped sudoers rule granting passwordless execution **only** to `dmidecode`:

```bash
sudo bash scripts/setup_sudoers.sh $USER
```

This creates `/etc/sudoers.d/hw-assistant`:
```text
<your_username> ALL=(ALL) NOPASSWD: /usr/sbin/dmidecode
```

### Non-Interactive Sudo Guard:
The executor invokes `sudo -n /usr/sbin/dmidecode`. The `-n` flag prevents sudo from prompting for passwords in non-interactive sessions. If privileges are missing, the assistant returns a structured warning rather than crashing or hanging.

---

## 🛡️ Privacy: Cloud vs. Local Inference

| Feature | Mode A: Claude API | Mode B: Local Ollama | Mode C: Mock Simulator |
|---|---|---|---|
| **Inference Location** | Anthropic Cloud | 100% On-Device | 100% On-Device |
| **Hardware Data Leaves Host?** | Yes (Only verified JSON sent) | **No** (Zero network egress) | **No** |
| **Internet Required?** | Yes | No | No |
| **Recommended Model** | `claude-3-5-sonnet-20241022` | `qwen2.5:7b` / `llama3.2:3b` | Built-in |
| **Best For** | High-precision cloud demos | Strict privacy & offline laptops | CI/CD testing & quick evaluation |

---

## 🧪 Testing & Verification

The project includes an extensive automated test suite covering all security checks, output parsers, anti-hallucination guardrails, and API endpoints.

Run the test suite:

```bash
python -m pytest -v
```

### Test Suite Coverage:
- `test_security.py`: Verifies allow-list enforcement, rejection of injected commands (`rm -rf`, `whoami`, `get_cpu_info; id`), `shell=False` compliance, timeouts, and missing binary handling.
- `test_parsers.py`: Validates parsing logic for `lscpu`, `free`, `lsblk -J`, `dmidecode -t memory`, `lspci -nnmm`, `nvidia-smi`, and `/sys/class/dmi/id`.
- `test_orchestration.py`: Tests LLM tool selection, multi-turn follow-ups, cache reuse, and strict anti-hallucination verification (e.g. soldered RAM correctly reported as non-upgradable).
- `test_api.py`: Validates all FastAPI endpoints (`/health`, `/tools`, `/hardware/*`, `/chat`, `/chat/reset`).

---

## ⚠️ Known Limitations

1. **Virtual Machines / Hypervisors:** In some cloud VMs (AWS EC2, GCP Compute Engine, QEMU), hypervisors mask DMI tables, causing `dmidecode` to report generic or virtualized memory arrays.
2. **Apple Silicon / Non-x86 Architecture:** Commands like `dmidecode` are x86/ARM SMBIOS-specific. On Apple Silicon, native Linux utilities report through device-tree rather than DMI.
3. **Containerized Environments (Docker):** Containers running without `--privileged` or without mounting `/sys` and `/dev/mem` cannot access DMI memory topology.

