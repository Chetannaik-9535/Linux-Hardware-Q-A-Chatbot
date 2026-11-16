"""Automated tests for FastAPI REST endpoints."""

from fastapi.testclient import TestClient
from hw_assistant.api.app import app

client = TestClient(app)


def test_api_health():
    """Verify health endpoint returns status online."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "version" in data
    assert "is_mock_enabled" in data


def test_api_tools_list():
    """Verify list of allow-listed tools."""
    res = client.get("/tools")
    assert res.status_code == 200
    tools = res.json()
    tool_names = [t["name"] for t in tools]
    assert "get_cpu_info" in tool_names
    assert "get_memory_info" in tool_names
    assert "get_memory_topology" in tool_names
    assert "get_storage_info" in tool_names
    assert "get_gpu_info" in tool_names


def test_api_hardware_endpoints():
    """Verify direct hardware inspection endpoints."""
    # CPU
    cpu_res = client.get("/hardware/cpu")
    assert cpu_res.status_code == 200
    assert "cores" in cpu_res.json()

    # Memory
    mem_res = client.get("/hardware/memory")
    assert mem_res.status_code == 200
    assert "total_gb" in mem_res.json()

    # Topology
    topo_res = client.get("/hardware/memory-topology")
    assert topo_res.status_code == 200
    assert "upgrade_assessment" in topo_res.json()

    # Storage
    store_res = client.get("/hardware/storage")
    assert store_res.status_code == 200
    assert "devices" in store_res.json()

    # GPU
    gpu_res = client.get("/hardware/gpu")
    assert gpu_res.status_code == 200
    assert isinstance(gpu_res.json(), list)

    # Motherboard
    mobo_res = client.get("/hardware/motherboard")
    assert mobo_res.status_code == 200


def test_api_chat_flow():
    """Verify /chat endpoint returns grounded responses with tool execution traces."""
    payload = {
        "message": "How much RAM do I have?",
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "message" in data
    assert len(data["message"]) > 0
    assert "session_id" in data
    assert "tool_traces" in data
    assert len(data["tool_traces"]) >= 1
    assert data["tool_traces"][0]["tool_name"] == "get_memory_info"

    # Reset session
    reset_res = client.post(f"/chat/reset?session_id={data['session_id']}")
    assert reset_res.status_code == 200

