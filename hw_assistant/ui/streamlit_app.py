"""Streamlit web chat interface for Linux Hardware Q&A Assistant.

Featuring a high-performance, dark cyberpunk aesthetic with glossy emerald green accents,
glassmorphism telemetry cards, and real-time tool execution traces.
"""

from __future__ import annotations

import uuid
import streamlit as st

from hw_assistant.config import settings
from hw_assistant.inspectors.cpu import CPUInspector
from hw_assistant.inspectors.gpu import GPUInspector
from hw_assistant.inspectors.memory import MemoryInspector
from hw_assistant.inspectors.storage import StorageInspector
from hw_assistant.mock_data.profiles import PROFILES
from hw_assistant.orchestration.dispatcher import ToolDispatcher
from hw_assistant.orchestration.engine import HardwareAssistantEngine
from hw_assistant.orchestration.providers.claude import ClaudeProvider
from hw_assistant.orchestration.providers.mock import MockProvider
from hw_assistant.orchestration.providers.ollama import OllamaProvider
from hw_assistant.security.executor import SafeCommandExecutor

# Configure Streamlit page layout
st.set_page_config(
    page_title="Linux Hardware AI Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Cyberpunk Dark Black & Glossy Emerald Green Theme
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* Main Background with Dark Carbon Grid & Radial Emerald Glow */
.stApp {
    background-color: #07090e;
    background-image:
        radial-gradient(at 10% 10%, rgba(0, 255, 136, 0.07) 0px, transparent 45%),
        radial-gradient(at 90% 90%, rgba(16, 185, 129, 0.05) 0px, transparent 50%),
        linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, sans-serif;
}

/* Sidebar Dark Glassmorphism */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #090d12 0%, #06080b 100%) !important;
    border-right: 1px solid rgba(0, 255, 136, 0.15) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.6);
}

/* Header Banner */
.header-container {
    background: linear-gradient(135deg, rgba(13, 20, 27, 0.85) 0%, rgba(7, 11, 15, 0.95) 100%);
    border: 1px solid rgba(0, 255, 136, 0.25);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(0, 255, 136, 0.4);
    position: relative;
    overflow: hidden;
}
.header-container::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #05d672, #00ff88, #38ef7d, transparent);
    box-shadow: 0 0 15px #00ff88;
}
.header-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 255, 136, 0.12);
    border: 1px solid rgba(0, 255, 136, 0.35);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.header-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #ffffff;
    margin: 6px 0;
    letter-spacing: -0.5px;
}
.green-gradient-text {
    background: linear-gradient(135deg, #00ff88 0%, #10b981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 25px rgba(0, 255, 136, 0.3);
}
.header-desc {
    color: #94a3b8;
    font-size: 0.95rem;
    margin: 0;
}

/* Glassmorphism Top Metric Cards */
.metric-card {
    background: linear-gradient(135deg, rgba(15, 23, 31, 0.8) 0%, rgba(8, 13, 17, 0.9) 100%);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(0, 255, 136, 0.25);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00ff88, transparent);
    opacity: 0.4;
}
.metric-card:hover {
    border-color: rgba(0, 255, 136, 0.55);
    transform: translateY(-2px);
    box-shadow: 0 12px 36px rgba(0, 255, 136, 0.16), inset 0 1px 0 rgba(0, 255, 136, 0.6);
}
.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.metric-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #6ee7b7;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.metric-icon {
    font-size: 1.15rem;
}
.metric-value {
    font-size: 1.45rem;
    font-weight: 800;
    color: #ffffff;
    text-shadow: 0 0 14px rgba(0, 255, 136, 0.35);
    margin: 4px 0 6px 0;
    font-family: 'JetBrains Mono', monospace;
}
.metric-sub {
    font-size: 0.8rem;
    color: #94a3b8;
    line-height: 1.35;
}
.metric-accent {
    color: #00ff88;
    font-weight: 600;
}

/* Tool Execution Tags (Terminal Style) */
.tool-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 255, 136, 0.12);
    color: #00ff88;
    border: 1px solid rgba(0, 255, 136, 0.35);
    padding: 3px 10px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 6px;
    box-shadow: 0 0 8px rgba(0, 255, 136, 0.15);
}

/* Streamlit Button Styling (Glossy Green Borders) */
div.stButton > button {
    background: linear-gradient(135deg, rgba(16, 26, 22, 0.85) 0%, rgba(9, 15, 12, 0.95) 100%) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(0, 255, 136, 0.28) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    padding: 10px 14px !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45) !important;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0, 255, 136, 0.18) 0%, rgba(5, 214, 114, 0.08) 100%) !important;
    color: #00ff88 !important;
    border-color: #00ff88 !important;
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.35) !important;
    transform: translateY(-1px) !important;
}

/* Chat Input Styling */
div[data-testid="stChatInput"] {
    background: rgba(13, 20, 27, 0.95) !important;
    border: 1px solid rgba(0, 255, 136, 0.35) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 25px rgba(0, 255, 136, 0.12) !important;
}
div[data-testid="stChatInput"]:focus-within {
    border-color: #00ff88 !important;
    box-shadow: 0 0 30px rgba(0, 255, 136, 0.3) !important;
}

/* Expander Glassmorphism */
div[data-testid="stExpander"] {
    background: rgba(11, 17, 23, 0.8) !important;
    border: 1px solid rgba(0, 255, 136, 0.2) !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

/* Status Widget */
div[data-testid="stStatusWidget"] {
    background: rgba(11, 18, 24, 0.9) !important;
    border: 1px solid rgba(0, 255, 136, 0.3) !important;
    border-radius: 10px !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #080c10;
}
::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 136, 0.25);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 136, 0.5);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_engine(mock_profile: str, provider_name: str) -> HardwareAssistantEngine:
    """Build or retrieve engine cached in session state."""
    executor = SafeCommandExecutor(mock_profile=mock_profile)
    dispatcher = ToolDispatcher(executor=executor)

    if provider_name == "Claude API":
        try:
            provider = ClaudeProvider()
        except Exception:
            st.sidebar.error("Anthropic API key missing or invalid. Falling back to Mock.")
            provider = MockProvider()
    elif provider_name == "Ollama (Local)":
        provider = OllamaProvider()
    else:
        provider = MockProvider()

    return HardwareAssistantEngine(
        provider=provider,
        dispatcher=dispatcher,
        executor=executor,
    )


# -----------------------------------------------------------------------------
# SIDEBAR: Configuration & Hardware Telemetry
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="font-size: 1.8rem;">⚡</span>
            <div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #ffffff; letter-spacing: -0.3px;">
                    HARDWARE <span style="color: #00ff88;">AI</span>
                </div>
                <div style="font-size: 0.72rem; color: #6ee7b7; text-transform: uppercase; letter-spacing: 1px;">
                    Linux Kernel Assistant
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### ⚙️ Engine Settings")

    provider_choice = st.selectbox(
        "LLM Provider Backend",
        options=["Mock (Deterministic/Offline)", "Claude API", "Ollama (Local)"],
        index=0,
    )

    # Privacy badge
    if provider_choice == "Claude API":
        st.info("☁️ **Cloud Mode:** Verified hardware JSON metrics are sent to the Anthropic Claude API.")
    elif provider_choice == "Ollama (Local)":
        st.success("🔒 **100% On-Device:** Air-gapped local inference via Ollama. Zero network egress.")
    else:
        st.success("⚡ **Mock Simulator:** Instant deterministic offline execution for rapid testing.")

    # Hardware Profile Selector
    is_mock = settings.is_mock_enabled
    st.markdown("---")
    st.markdown("### 🖥️ Machine Profile")
    if is_mock:
        st.caption("Simulating genuine Linux utilities (`lscpu`, `free`, `lsblk`, `dmidecode`).")
        active_profile = st.selectbox(
            "Hardware Profile",
            options=list(PROFILES.keys()),
            format_func=lambda x: {
                "thinkpad_x1": "Lenovo ThinkPad X1 (16GB Soldered, i7-1260P)",
                "dell_xps": "Dell XPS 15 (32GB DDR5 2/2, RTX 3050Ti)",
                "gaming_desktop": "Custom Desktop (32GB DDR4 2/4, RTX 4080)",
                "acer_budget": "Acer Budget (8GB DDR4 1/1, Ryzen 3)",
            }.get(x, x),
            index=0,
        )
    else:
        active_profile = settings.mock_profile
        st.success("🐧 Native Linux host detected! Using live OS system utilities.")

    st.markdown("---")
    if st.button("🗑️ Clear Session Memory", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Instantiate Engine
engine = get_engine(active_profile, provider_choice)

# -----------------------------------------------------------------------------
# HERO BANNER
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="header-container">
        <div class="header-badge">
            <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #00ff88; box-shadow: 0 0 8px #00ff88;"></span>
            KERNEL VERIFIED • ZERO HALLUCINATIONS
        </div>
        <div class="header-title">
            LINUX HARDWARE <span class="green-gradient-text">Q&A ASSISTANT</span>
        </div>
        <p class="header-desc">
            Direct system inspection using native Linux tools (<code>lscpu</code>, <code>free</code>, <code>lsblk</code>, <code>dmidecode</code>) with safe LLM tool-calling.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# TOP GLOSSY TELEMETRY CARDS (CPU, RAM, STORAGE, GPU)
# -----------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

try:
    cpu_info = CPUInspector(engine.executor).inspect()
    mem_info = MemoryInspector(engine.executor).inspect()
    storage_info = StorageInspector(engine.executor).inspect()
    gpu_list = GPUInspector(engine.executor).inspect()

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Processor (CPU)</span>
                    <span class="metric-icon">⚡</span>
                </div>
                <div class="metric-value">{cpu_info.cores}C / {cpu_info.threads}T</div>
                <div class="metric-sub">{cpu_info.model}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">System Memory (RAM)</span>
                    <span class="metric-icon">🧠</span>
                </div>
                <div class="metric-value">{mem_info.total_gb:.1f} GB</div>
                <div class="metric-sub">
                    <span class="metric-accent">{mem_info.utilization_percent}%</span> used • {mem_info.available_gb:.1f} GB available
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Storage Media</span>
                    <span class="metric-icon">💽</span>
                </div>
                <div class="metric-value">{storage_info.total_disks} Drive(s)</div>
                <div class="metric-sub">
                    <span class="metric-accent">{storage_info.nvme_count} NVMe SSD</span> • {storage_info.sata_count} SATA
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        gpu_name = gpu_list[0].model if gpu_list else "Integrated Graphics"
        vram_str = f"{gpu_list[0].vram_mb} MB VRAM" if gpu_list and gpu_list[0].vram_mb else "Shared VRAM"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-title">Graphics (GPU)</span>
                    <span class="metric-icon">🎮</span>
                </div>
                <div class="metric-value">{gpu_name}</div>
                <div class="metric-sub">{vram_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
except Exception as e:
    st.warning(f"Hardware telemetry preview error: {e}")

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# QUICK QUESTION ACTION CHIPS
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #6ee7b7; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>💡 Quick Hardware Inquiries</div>", unsafe_allow_html=True)
qcols = st.columns(6)
chips = [
    ("How much RAM do I have?", qcols[0]),
    ("Can I upgrade my RAM?", qcols[1]),
    ("What CPU am I using?", qcols[2]),
    ("Is my SSD NVMe or SATA?", qcols[3]),
    ("What GPU is installed?", qcols[4]),
    ("Full system summary", qcols[5]),
]

selected_query = None
for text, col in chips:
    if col.button(text, use_container_width=True):
        selected_query = text

st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CHAT INTERFACE & TOOL TRACES
# -----------------------------------------------------------------------------
st.markdown("<div style='font-size: 0.95rem; font-weight: 700; color: #e2e8f0; margin-bottom: 12px;'>💬 Hardware Conversation</div>", unsafe_allow_html=True)

# Display historical messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_traces"):
            with st.expander("🔍 Verified Tool Execution Traces"):
                for trace in msg["tool_traces"]:
                    st.markdown(
                        f"<span class='tool-tag'>[✓] {trace.get('tool_name')}</span> "
                        f"<span style='color: #6ee7b7; font-family: monospace; font-size: 0.8rem;'>⏱️ {trace.get('execution_time_ms', 0):.1f}ms</span>",
                        unsafe_allow_html=True,
                    )
                    if trace.get("permission_note"):
                        st.warning(trace["permission_note"])
                    st.json(trace.get("data") or {"error": trace.get("error")})

# Chat input prompt
user_prompt = st.chat_input("Ask about your hardware (e.g. 'Can I upgrade my RAM?', 'What CPU do I have?')...")
prompt_to_process = selected_query or user_prompt

if prompt_to_process:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": prompt_to_process})
    with st.chat_message("user"):
        st.markdown(prompt_to_process)

    # Assistant response with tool execution status
    with st.chat_message("assistant"):
        with st.status("🔍 Inspecting Linux hardware utilities...", expanded=True) as status:
            response = engine.ask(
                query=prompt_to_process,
                session_id=st.session_state.session_id,
            )

            if response.tool_traces:
                for trace in response.tool_traces:
                    status.write(f"Executed allow-listed tool: `{trace.tool_name}` in {trace.execution_time_ms:.1f}ms")
                status.update(label="Hardware verified! Grounded response generated.", state="complete", expanded=False)
            else:
                status.update(label="Response generated.", state="complete", expanded=False)

        st.markdown(response.message)

        # Show tool trace details
        if response.tool_traces:
            with st.expander("🔍 Verified Tool Execution Traces"):
                for trace in response.tool_traces:
                    st.markdown(
                        f"<span class='tool-tag'>[✓] {trace.tool_name}</span> "
                        f"<span style='color: #6ee7b7; font-family: monospace; font-size: 0.8rem;'>⏱️ {trace.execution_time_ms:.1f}ms</span>",
                        unsafe_allow_html=True,
                    )
                    if trace.permission_note:
                        st.warning(trace.permission_note)
                    st.json(trace.data or {"error": trace.error})

    # Save to history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.message,
            "tool_traces": [t.model_dump() for t in response.tool_traces],
        }
    )
