"""API tests for the bounded development checkout session."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.v1.checkout_sessions as checkout_sessions
from app.api.dependencies import get_authenticated_credential, get_db_session
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.models.payment_intent import PaymentIntent
from app.models.payment_method import PaymentMethod
from app.services.checkout_session import DemoCheckoutResult

client = TestClient(app)


def override_get_db_session():
    yield object()


def test_checkout_session_uses_authenticated_merchant_and_no_card_payload(
    monkeypatch,
) -> None:
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    method_id = uuid.uuid4()
    now = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )
    payment = PaymentIntent(
        id=payment_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=method_id,
        external_reference="century-order-123",
        amount_minor=125000,
        currency="USD",
        status="succeeded",
        created_at=now,
        updated_at=now,
    )
    method = PaymentMethod(
        id=method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2099,
        status="active",
        test_scenario="success",
        created_at=now,
        updated_at=now,
    )
    received: dict[str, object] = {}

    def fake_create(**kwargs):
        received.update(kwargs)
        return DemoCheckoutResult(
            payment_intent=payment,
            payment_method=method,
        )

    monkeypatch.setattr(
        checkout_sessions,
        "create_demo_checkout_session",
        fake_create,
    )
    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    payload = {
        "customer_external_reference": "century-customer-123",
        "customer_display_name": "Century Customer",
        "customer_email": "customer@example.com",
        "external_reference": "century-order-123",
        "amount_minor": 125000,
        "currency": "USD",
        "test_scenario": "success",
    }

    try:
        response = client.post(
            "/api/v1/checkout-sessions",
            headers={"Idempotency-Key": "century-payment-123"},
            json=payload,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["payment_intent_id"] == str(payment_id)
    assert response.json()["payment_method"] == {
        "type": "card",
        "brand": "visa",
        "last4": "4242",
    }
    assert received["merchant_id"] == merchant_id
    assert received["idempotency_key"] == "century-payment-123"
    assert not any(
        key in payload
        for key in {
            "card_number",
            "pan",
            "cvv",
            "cvc",
            "expiration",
            "exp_month",
            "exp_year",
        }
    )


def test_checkout_session_requires_idempotency_key() -> None:
    response = client.post(
        "/api/v1/checkout-sessions",
        json={
            "customer_external_reference": "century-customer-123",
            "customer_display_name": "Century Customer",
            "customer_email": "customer@example.com",
            "external_reference": "century-order-123",
            "amount_minor": 125000,
            "currency": "USD",
            "test_scenario": "success",
        },
    )

    assert response.status_code in {401, 422}
