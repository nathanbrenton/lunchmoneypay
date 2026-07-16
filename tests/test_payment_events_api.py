"""Tests for payment-event API endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.v1.payment_events as payment_events
from app.api.dependencies import (
    get_authenticated_credential,
    get_db_session,
)
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.models.payment_event import PaymentEvent

client = TestClient(app)


def override_get_db_session():
    """Provide a lightweight fake database dependency."""

    yield object()


def test_get_payment_event_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Retrieve a payment event within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    payment_event_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_event = PaymentEvent(
        id=payment_event_id,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        event_type="payment_intent.succeeded",
        payload={
            "status": "succeeded",
        },
        created_at=timestamp,
    )

    received_arguments = {}

    def fake_get_payment_event(
        session,
        merchant_id,
        payment_event_id,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_event_id"] = payment_event_id
        return payment_event

    monkeypatch.setattr(
        payment_events,
        "get_payment_event",
        fake_get_payment_event,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            f"/api/v1/payment-events/{payment_event_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": str(payment_event_id),
        "merchant_id": str(merchant_id),
        "payment_intent_id": str(payment_intent_id),
        "event_type": "payment_intent.succeeded",
        "payload": {
            "status": "succeeded",
        },
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
    }

    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_event_id": payment_event_id,
    }


def test_get_payment_event_returns_not_found(
    monkeypatch,
) -> None:
    """Return 404 when the payment event is missing or inaccessible."""

    merchant_id = uuid.uuid4()
    payment_event_id = uuid.uuid4()

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
        payment_event_id,
    ):
        raise payment_events.PaymentEventNotFoundError(
            payment_event_id,
        )

    monkeypatch.setattr(
        payment_events,
        "get_payment_event",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            f"/api/v1/payment-events/{payment_event_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Payment event not found.",
    }


def test_list_payment_events_uses_authenticated_merchant_and_returns_empty_list(
    monkeypatch,
) -> None:
    """List payment events within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    received_merchant_ids: list[uuid.UUID] = []

    def fake_list_payment_events(
        session,
        merchant_id,
        payment_intent_id=None,
        event_type=None,
    ):
        received_merchant_ids.append(merchant_id)
        assert payment_intent_id is None
        assert event_type is None
        return []

    monkeypatch.setattr(
        payment_events,
        "list_payment_events",
        fake_list_payment_events,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get("/api/v1/payment-events")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    assert received_merchant_ids == [merchant_id]


def test_list_payment_events_returns_serialized_records(
    monkeypatch,
) -> None:
    """Return merchant payment events as PaymentEventRead records."""

    merchant_id = uuid.uuid4()
    payment_event_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_event = PaymentEvent(
        id=payment_event_id,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        event_type="payment_intent.payment_failed",
        payload={
            "id": str(payment_intent_id),
            "status": "requires_payment_method",
            "last_error_code": "card_declined",
        },
        created_at=timestamp,
    )

    monkeypatch.setattr(
        payment_events,
        "list_payment_events",
        lambda session, merchant_id, payment_intent_id=None, event_type=None: [
            payment_event
        ],
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get("/api/v1/payment-events")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(payment_event_id),
            "merchant_id": str(merchant_id),
            "payment_intent_id": str(payment_intent_id),
            "event_type": "payment_intent.payment_failed",
            "payload": {
                "id": str(payment_intent_id),
                "status": "requires_payment_method",
                "last_error_code": "card_declined",
            },
            "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        },
    ]


def test_list_payment_events_filters_by_payment_intent(
    monkeypatch,
) -> None:
    """Pass the optional payment-intent filter to the service."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    received_arguments = {}

    def fake_list_payment_events(
        session,
        merchant_id,
        payment_intent_id=None,
        event_type=None,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        received_arguments["event_type"] = event_type
        return []

    monkeypatch.setattr(
        payment_events,
        "list_payment_events",
        fake_list_payment_events,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            "/api/v1/payment-events",
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
        "event_type": None,
    }


def test_list_payment_events_filters_by_event_type(
    monkeypatch,
) -> None:
    """Pass the optional event-type filter to the service."""

    merchant_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    received_arguments = {}

    def fake_list_payment_events(
        session,
        merchant_id,
        payment_intent_id=None,
        event_type=None,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        received_arguments["event_type"] = event_type
        return []

    monkeypatch.setattr(
        payment_events,
        "list_payment_events",
        fake_list_payment_events,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            "/api/v1/payment-events",
            params={
                "event_type": "payment_intent.payment_failed",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_intent_id": None,
        "event_type": "payment_intent.payment_failed",
    }
