"""Tests for merchant API credential endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1 import merchant_api_credentials
from app.db.session import get_db_session
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.services.merchant_api_credential import CreatedMerchantApiCredential

client = TestClient(app)


def override_get_db_session():
    """Provide a mocked database session for API tests."""

    yield MagicMock(spec=Session)


def test_create_merchant_api_credential_returns_one_time_key(
    monkeypatch,
) -> None:
    credential_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)
    api_key = "lmp_test_a1b2c3d4e5f6.example-secret"

    credential = MerchantApiCredential(
        id=credential_id,
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
        expires_at=None,
        created_at=timestamp,
    )

    monkeypatch.setattr(
        merchant_api_credentials,
        "create_merchant_api_credential",
        lambda session, merchant_id, pepper: CreatedMerchantApiCredential(
            credential=credential,
            api_key=api_key,
        ),
    )

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        response = client.post(
            f"/api/v1/merchants/{merchant_id}/credentials",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": str(credential_id),
        "merchant_id": str(merchant_id),
        "key_prefix": "lmp_test_a1b2c3d4e5f6",
        "status": "active",
        "expires_at": None,
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "api_key": api_key,
    }


def test_create_merchant_api_credential_returns_not_found(
    monkeypatch,
) -> None:
    merchant_id = uuid.uuid4()

    def raise_not_found(session, merchant_id, pepper):
        raise merchant_api_credentials.MerchantNotFoundError(merchant_id)

    monkeypatch.setattr(
        merchant_api_credentials,
        "create_merchant_api_credential",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        response = client.post(
            f"/api/v1/merchants/{merchant_id}/credentials",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Merchant not found.",
    }
