"""Tests for refund API endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.v1.refunds as refunds
from app.api.dependencies import (
    get_authenticated_credential,
    get_db_session,
)
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.models.refund import Refund

client = TestClient(app)


def override_get_db_session():
    """Provide a lightweight fake database dependency."""

    yield object()


def build_credential(
    merchant_id: uuid.UUID,
) -> MerchantApiCredential:
    """Build an authenticated merchant credential."""

    return MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )


def test_create_refund_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Create a refund within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    refund_id = uuid.uuid4()
    timestamp = datetime.now(UTC)
    credential = build_credential(merchant_id)

    refund = Refund(
        id=refund_id,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        external_reference="refund-123",
        amount_minor=1000,
        currency="USD",
        status="succeeded",
        created_at=timestamp,
    )

    received_arguments = {}

    def fake_create_refund(
        session,
        merchant_id,
        refund_create,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["refund_create"] = refund_create
        return refund

    monkeypatch.setattr(
        refunds,
        "create_refund",
        fake_create_refund,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/refunds",
            json={
                "payment_intent_id": str(payment_intent_id),
                "external_reference": "refund-123",
                "amount_minor": 1000,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(refund_id)
    assert response.json()["merchant_id"] == str(merchant_id)
    assert received_arguments["merchant_id"] == merchant_id


def test_create_refund_rejects_amount_above_available(
    monkeypatch,
) -> None:
    """Return conflict when a refund exceeds the available balance."""

    merchant_id = uuid.uuid4()
    credential = build_credential(merchant_id)

    def raise_invalid_amount(
        session,
        merchant_id,
        refund_create,
    ):
        raise refunds.RefundAmountExceedsAvailableError(
            refund_create.amount_minor,
        )

    monkeypatch.setattr(
        refunds,
        "create_refund",
        raise_invalid_amount,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/refunds",
            json={
                "payment_intent_id": str(uuid.uuid4()),
                "external_reference": "refund-123",
                "amount_minor": 3000,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Refund amount exceeds the remaining refundable amount.",
    }


def test_get_refund_returns_not_found(
    monkeypatch,
) -> None:
    """Return 404 for a missing or merchant-inaccessible refund."""

    merchant_id = uuid.uuid4()
    refund_id = uuid.uuid4()
    credential = build_credential(merchant_id)

    def raise_not_found(
        session,
        merchant_id,
        refund_id,
    ):
        raise refunds.RefundNotFoundError(refund_id)

    monkeypatch.setattr(
        refunds,
        "get_refund",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            f"/api/v1/refunds/{refund_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Refund not found.",
    }


def test_list_refunds_forwards_payment_intent_filter(
    monkeypatch,
) -> None:
    """Forward merchant and payment-intent filtering to the service."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    credential = build_credential(merchant_id)
    received_arguments = {}

    def fake_list_refunds(
        session,
        merchant_id,
        payment_intent_id=None,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        return []

    monkeypatch.setattr(
        refunds,
        "list_refunds",
        fake_list_refunds,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            "/api/v1/refunds",
            params={
                "payment_intent_id": str(payment_intent_id),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_intent_id": payment_intent_id,
    }
