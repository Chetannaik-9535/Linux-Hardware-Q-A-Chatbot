"""FastAPI backend service exposing hardware inspection and LLM chat endpoints."""

from __future__ import annotations

import platform
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from hw_assistant import __version__
from hw_assistant.config import settings
from hw_assistant.inspectors.cpu import CPUInspector
from hw_assistant.inspectors.gpu import GPUInspector
from hw_assistant.inspectors.memory import MemoryInspector
from hw_assistant.inspectors.memory_topology import MemoryTopologyInspector
from hw_assistant.inspectors.motherboard import MotherboardInspector
from hw_assistant.inspectors.storage import StorageInspector
from hw_assistant.inspectors.system import SystemSummaryInspector
from hw_assistant.models.chat import ChatRequest, ChatResponse
from hw_assistant.models.hardware import (
    CPUInfo,
    GPUInfo,
    MemoryInfo,
    MemoryTopology,
    MotherboardInfo,
    StorageInfo,
    SystemSummary,
)
from hw_assistant.models.tools import HARDWARE_TOOLS
from hw_assistant.orchestration.engine import default_engine

app = FastAPI(
    title="Linux Hardware Q&A Assistant API",
    version=__version__,
    description="A safe, verified Linux hardware assistant API with LLM tool-calling orchestration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def get_health() -> dict[str, str | bool]:
    """Health check endpoint indicating service status and inspection mode."""
    return {
        "status": "online",
        "version": __version__,
        "platform": platform.platform(),
        "is_native_linux": settings.is_linux,
        "is_mock_enabled": settings.is_mock_enabled,
        "active_mock_profile": settings.mock_profile,
        "llm_provider": settings.llm_provider,
    }


@app.get("/tools", tags=["Tools"])
def list_tools() -> list[dict]:
    """List all safe allow-listed hardware inspection tools exposed to LLMs."""
    return [t.model_dump() for t in HARDWARE_TOOLS]


@app.get("/hardware/summary", response_model=SystemSummary, tags=["Hardware"])
def get_system_summary() -> SystemSummary:
    """Retrieve full system hardware overview."""
    return SystemSummaryInspector().inspect()


@app.get("/hardware/cpu", response_model=CPUInfo, tags=["Hardware"])
def get_cpu() -> CPUInfo:
    """Retrieve verified CPU specifications."""
    return CPUInspector().inspect()


@app.get("/hardware/memory", response_model=MemoryInfo, tags=["Hardware"])
def get_memory() -> MemoryInfo:
    """Retrieve real-time memory usage statistics."""
    return MemoryInspector().inspect()


@app.get("/hardware/memory-topology", response_model=MemoryTopology, tags=["Hardware"])
def get_memory_topology() -> MemoryTopology:
    """Retrieve physical RAM slots, module details, and upgrade limits."""
    return MemoryTopologyInspector().inspect()


@app.get("/hardware/storage", response_model=StorageInfo, tags=["Hardware"])
def get_storage() -> StorageInfo:
    """Retrieve disk drives, SSD/HDD classifications, and partition trees."""
    return StorageInspector().inspect()


@app.get("/hardware/gpu", response_model=list[GPUInfo], tags=["Hardware"])
def get_gpu() -> list[GPUInfo]:
    """Retrieve detected graphics cards, drivers, and VRAM."""
    return GPUInspector().inspect()


@app.get("/hardware/motherboard", response_model=MotherboardInfo, tags=["Hardware"])
def get_motherboard() -> MotherboardInfo:
    """Retrieve motherboard manufacturer, model, and BIOS version."""
    return MotherboardInspector().inspect()


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest) -> ChatResponse:
    """Ask a natural-language hardware question and get a verified, grounded answer."""
    try:
        response = default_engine.ask(
            query=request.message,
            session_id=request.session_id,
            force_refresh=request.force_refresh,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant execution error: {str(e)}")


@app.post("/chat/reset", tags=["Chat"])
def reset_chat_session(session_id: str) -> dict[str, str]:
    """Clear conversation history and hardware cache for a session."""
    default_engine.reset_session(session_id)
    return {"status": "success", "message": f"Session '{session_id}' reset."}

