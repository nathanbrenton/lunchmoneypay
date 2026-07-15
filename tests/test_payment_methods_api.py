"""Tests for payment-method API endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.v1.payment_methods as payment_methods
from app.api.dependencies import (
    get_authenticated_credential,
    get_db_session,
)
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.models.payment_method import PaymentMethod

client = TestClient(app)


def override_get_db_session():
    """Provide a lightweight fake database dependency."""

    yield object()


def test_create_payment_method_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Create a mock card within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_create_payment_method(
        session,
        merchant_id,
        payment_method_create,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_method_create"] = payment_method_create
        return payment_method

    monkeypatch.setattr(
        payment_methods,
        "create_payment_method",
        fake_create_payment_method,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/payment-methods",
            json={
                "customer_id": str(customer_id),
                "card_brand": "visa",
                "card_last4": "4242",
                "card_exp_month": 12,
                "card_exp_year": 2030,
                "test_scenario": "success",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(payment_method_id)
    assert response.json()["merchant_id"] == str(merchant_id)
    assert response.json()["type"] == "card"
    assert response.json()["status"] == "active"

    assert received_arguments["merchant_id"] == merchant_id
    assert received_arguments["payment_method_create"].model_dump() == {
        "customer_id": customer_id,
        "card_brand": "visa",
        "card_last4": "4242",
        "card_exp_month": 12,
        "card_exp_year": 2030,
        "test_scenario": "success",
    }


def test_create_payment_method_returns_not_found_for_invalid_customer(
    monkeypatch,
) -> None:
    """Return 404 when the customer is missing or merchant-inaccessible."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_not_found(
        session,
        merchant_id,
        payment_method_create,
    ):
        raise payment_methods.CustomerNotFoundError(
            payment_method_create.customer_id,
        )

    monkeypatch.setattr(
        payment_methods,
        "create_payment_method",
        raise_not_found,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/payment-methods",
            json={
                "customer_id": str(customer_id),
                "card_brand": "visa",
                "card_last4": "4242",
                "card_exp_month": 12,
                "card_exp_year": 2030,
                "test_scenario": "success",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Customer not found.",
    }
