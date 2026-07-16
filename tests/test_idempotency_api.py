"""API tests for idempotent create requests."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.v1.payment_intents as payment_intents
import app.api.v1.refunds as refunds
from app.api.dependencies import get_authenticated_credential, get_db_session
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.models.payment_intent import PaymentIntent

client = TestClient(app)


def override_get_db_session():
    """Provide a lightweight fake database dependency."""

    yield object()


def credential(merchant_id: uuid.UUID) -> MerchantApiCredential:
    """Build an authenticated merchant credential."""

    return MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )


def test_payment_create_forwards_idempotency_key(monkeypatch) -> None:
    """Forward the request idempotency key to the payment service."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    timestamp = datetime.now(UTC)
    received = {}
    payment = PaymentIntent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="payment-123",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        created_at=timestamp,
        updated_at=timestamp,
    )

    def fake_create(session, merchant_id, payment_intent_create, idempotency_key=None):
        received["key"] = idempotency_key
        return payment

    monkeypatch.setattr(payment_intents, "create_payment_intent", fake_create)
    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential(
        merchant_id
    )
    try:
        response = client.post(
            "/api/v1/payment-intents",
            headers={"Idempotency-Key": "create-payment-123"},
            json={
                "customer_id": str(customer_id),
                "external_reference": "payment-123",
                "amount_minor": 2500,
                "currency": "USD",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert received["key"] == "create-payment-123"


def test_refund_create_returns_conflict_for_key_reuse(monkeypatch) -> None:
    """Translate an idempotency mismatch into HTTP 409."""

    merchant_id = uuid.uuid4()

    def raise_conflict(session, merchant_id, refund_create, idempotency_key=None):
        raise refunds.IdempotencyKeyConflictError(idempotency_key)

    monkeypatch.setattr(refunds, "create_refund", raise_conflict)
    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential(
        merchant_id
    )
    try:
        response = client.post(
            "/api/v1/refunds",
            headers={"Idempotency-Key": "refund-123"},
            json={
                "payment_intent_id": str(uuid.uuid4()),
                "external_reference": "refund-123",
                "amount_minor": 500,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Idempotency key was already used for a different request."
    }
