"""Tests for LunchMoneyPay health and readiness endpoints."""

from fastapi.testclient import TestClient

from app.api.v1 import health
from app.main import app

client = TestClient(app)


def test_root_returns_running_message() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "LunchMoneyPay is running",
    }


def test_health_returns_service_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "LunchMoneyPay",
        "environment": "development",
    }


def test_readiness_returns_ready_when_database_is_available(
    monkeypatch,
) -> None:
    monkeypatch.setattr(health, "database_is_ready", lambda: True)

    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "available",
    }


def test_readiness_returns_503_when_database_is_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(health, "database_is_ready", lambda: False)

    response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "unavailable",
    }
