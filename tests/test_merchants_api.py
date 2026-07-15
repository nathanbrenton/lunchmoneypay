"""Tests for merchant API endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1 import merchants
from app.db.session import get_db_session
from app.main import app
from app.models.merchant import Merchant

client = TestClient(app)


def override_get_db_session():
    """Provide a mocked database session for API tests."""

    yield MagicMock(spec=Session)


def test_create_merchant_returns_created_merchant(
    monkeypatch,
) -> None:
    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    merchant = Merchant(
        id=merchant_id,
        name="Homesteady",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    monkeypatch.setattr(
        merchants,
        "create_merchant",
        lambda session, merchant_create: merchant,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        response = client.post(
            "/api/v1/merchants",
            json={"name": "Homesteady"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": str(merchant_id),
        "name": "Homesteady",
        "status": "active",
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "updated_at": timestamp.isoformat().replace("+00:00", "Z"),
    }


def test_create_merchant_returns_conflict_for_duplicate(
    monkeypatch,
) -> None:
    def raise_duplicate(session, merchant_create):
        raise merchants.MerchantAlreadyExistsError(merchant_create.name)

    monkeypatch.setattr(
        merchants,
        "create_merchant",
        raise_duplicate,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        response = client.post(
            "/api/v1/merchants",
            json={"name": "Homesteady"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A merchant with this name already exists.",
    }
