"""Smoke tests for all API endpoints."""
import io

from fastapi.testclient import TestClient
from PIL import Image

from am180.api import app

client = TestClient(app)


# --- GET /api/generators ---

def test_list_generators() -> None:
    response = client.get("/api/generators")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    hello = next(g for g in data if g["id"] == "hello")
    assert hello["name"] == "Hello"
    assert "description" in hello


# --- GET /api/generators/{id}/schema ---

def test_get_schema() -> None:
    response = client.get("/api/generators/hello/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "hello"
    assert data["name"] == "Hello"
    assert isinstance(data["params"], list)
    color_param = next(p for p in data["params"] if p["id"] == "color")
    assert color_param["type"] == "color"
    assert color_param["default"] == "#ff0000"


def test_get_schema_unknown_generator() -> None:
    response = client.get("/api/generators/nonexistent/schema")
    assert response.status_code == 404


# --- POST /api/preview ---

def test_preview_returns_png() -> None:
    response = client.post(
        "/api/preview?size=64",
        json={"generator": "hello", "params": {"color": "#ff0000"}, "seed": 42},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(response.content))
    assert img.size == (64, 64)


def test_preview_default_size() -> None:
    response = client.post(
        "/api/preview",
        json={"generator": "hello", "params": {"color": "#ff0000"}, "seed": 1},
    )
    assert response.status_code == 200
    img = Image.open(io.BytesIO(response.content))
    assert img.size == (512, 512)


def test_preview_unknown_generator() -> None:
    response = client.post(
        "/api/preview",
        json={"generator": "nonexistent", "params": {}, "seed": 0},
    )
    assert response.status_code == 404


def test_preview_rejects_oversize() -> None:
    response = client.post(
        "/api/preview?size=2048",
        json={"generator": "hello", "params": {"color": "#ff0000"}, "seed": 1},
    )
    assert response.status_code == 422


# --- POST /api/render ---

def test_render_returns_png_with_disposition() -> None:
    response = client.post(
        "/api/render?size=128",
        json={"generator": "hello", "params": {"color": "#00ff00"}, "seed": 77},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "attachment" in response.headers["content-disposition"]
    assert "hello-77.png" in response.headers["content-disposition"]
    img = Image.open(io.BytesIO(response.content))
    assert img.size == (128, 128)


# --- Determinism across preview and render ---

def test_same_params_same_seed_same_image() -> None:
    """Preview and render at the same size must return identical bytes."""
    body = {"generator": "hello", "params": {"color": "#abcdef"}, "seed": 123}
    r1 = client.post("/api/preview?size=64", json=body)
    r2 = client.post("/api/preview?size=64", json=body)
    assert r1.content == r2.content


# --- Health endpoint still works ---

def test_health_still_responds() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Flow field integration ---

def test_flow_field_preview() -> None:
    """The flow field generator must be accessible through the API."""
    response = client.post(
        "/api/preview?size=64",
        json={
            "generator": "flow_field",
            "params": {
                "noise_scale": 3.0,
                "angle_range": 1.0,
                "particle_density": 0.001,
                "step_size": 0.002,
                "max_steps": 50,
                "line_width": 0.0015,
                "background": "#0a0a14",
                "palette": "warm",
            },
            "seed": 42,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(response.content))
    assert img.size == (64, 64)


def test_flow_field_listed_in_generators() -> None:
    response = client.get("/api/generators")
    data = response.json()
    ids = [g["id"] for g in data]
    assert "flow_field" in ids


def test_flow_field_schema_endpoint() -> None:
    response = client.get("/api/generators/flow_field/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "flow_field"
    param_ids = [p["id"] for p in data["params"]]
    assert "noise_scale" in param_ids
    assert "palette" in param_ids
    assert len(data["params"]) == 9
