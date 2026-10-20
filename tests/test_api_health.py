"""Integration test for the health-check endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "PDF-ChatGPT"
    assert "openai_configured" in body
    assert "gemini_configured" in body
    assert body["gemini_configured"] is True


def test_docs_endpoint_is_available() -> None:
    # Standard FastAPI endpoints
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/redoc").status_code == 200

    # Aliased /api documentation endpoints
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/redoc").status_code == 200

