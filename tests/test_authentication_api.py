"""Tests for API-key authentication verification endpoints."""

import uuid

from fastapi.testclient import TestClient

from app.api.dependencies import get_authenticated_credential
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential

client = TestClient(app)


def test_whoami_returns_authenticated_context() -> None:
    credential_id = uuid.uuid4()
    merchant_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=credential_id,
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    app.dependency_overrides[get_authenticated_credential] = (
        lambda: credential
    )

    try:
        response = client.get("/api/v1/auth/whoami")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "merchant_id": str(merchant_id),
        "credential_id": str(credential_id),
        "key_prefix": "lmp_test_a1b2c3d4e5f6",
    }
