# (c) 2026 Liumi Corporation. All Rights Reserved. Private & Proprietary.

import pytest
from fastapi.testclient import TestClient
from liumify.core import LiumifyApp
from liumify.components import LiumifySphere, UI_GlassCard

def test_component_serialization():
    """Verify HD objects convert to JSON correctly."""
    sphere = LiumifySphere(radius=5.0)
    sphere.set_material("#FF0000", 0.5)
    
    data = sphere.serialize()
    
    assert data["type"] == "hd_sphere"
    assert data["props"]["radius"] == 5.0
    assert data["props"]["material"]["color"] == "#FF0000"

def test_scene_graph_integrity():
    """Verify the App controller registers components."""
    app = LiumifyApp("Test Suite")
    app.add(LiumifySphere())
    app.add(UI_GlassCard("Test", "Body"))
    
    # Internal method access for testing
    state = app._get_scene_state()
    assert len(state["scene"]) == 2
    assert state["meta"]["app_name"] == "Test Suite"

def test_engine_availability():
    """Verify the hidden rendering shell is serving HTML."""
    app = LiumifyApp("Server Test")
    client = TestClient(app._server)
    
    response = client.get("/")
    assert response.status_code == 200
    # Check if our proprietary HTML structure is present
    assert "Liumify HD" in response.text
    assert "render-target" in response.text