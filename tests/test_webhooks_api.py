"""Tests for webhook registration and delivery endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.v1.webhooks as webhooks
from app.api.dependencies import get_authenticated_credential, get_db_session
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.models.webhook_endpoint import WebhookEndpoint

client = TestClient(app)


def override_get_db_session():
    """Provide a lightweight fake database dependency."""

    yield object()


def build_credential(merchant_id: uuid.UUID) -> MerchantApiCredential:
    """Build an authenticated merchant credential."""

    return MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )


def test_create_webhook_endpoint_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Register an endpoint within the merchant boundary."""

    merchant_id = uuid.uuid4()
    endpoint_id = uuid.uuid4()
    timestamp = datetime.now(UTC)
    credential = build_credential(merchant_id)
    endpoint = WebhookEndpoint(
        id=endpoint_id,
        merchant_id=merchant_id,
        url="https://example.test/webhooks",
        signing_secret="a" * 32,
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    monkeypatch.setattr(
        webhooks,
        "create_webhook_endpoint",
        lambda session, merchant_id, endpoint_create: endpoint,
    )
    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/webhook-endpoints",
            json={
                "url": "https://example.test/webhooks",
                "signing_secret": "a" * 32,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(endpoint_id)
    assert "signing_secret" not in response.json()


def test_dispatch_endpoint_forwards_authenticated_merchant(
    monkeypatch,
) -> None:
    """Dispatch a persisted event within the merchant boundary."""

    merchant_id = uuid.uuid4()
    event_id = uuid.uuid4()
    credential = build_credential(merchant_id)
    received_arguments = {}

    def fake_deliver_payment_event(session, merchant_id, payment_event_id):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_event_id"] = payment_event_id
        return []

    monkeypatch.setattr(
        webhooks,
        "deliver_payment_event",
        fake_deliver_payment_event,
    )
    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/webhook-deliveries/payment-events/{event_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_event_id": event_id,
    }
