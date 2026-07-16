"""Tests for payment-intent API endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.api.v1.payment_intents as payment_intents
from app.api.dependencies import (
    get_authenticated_credential,
    get_db_session,
)
from app.main import app
from app.models.merchant_api_credential import MerchantApiCredential
from app.models.payment_intent import PaymentIntent

client = TestClient(app)


def override_get_db_session():
    """Provide a lightweight fake database dependency."""

    yield object()


def test_create_payment_intent_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Create a payment intent within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_create_payment_intent(
        session,
        merchant_id,
        payment_intent_create,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_create"] = payment_intent_create
        return payment_intent

    monkeypatch.setattr(
        payment_intents,
        "create_payment_intent",
        fake_create_payment_intent,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/payment-intents",
            json={
                "customer_id": str(customer_id),
                "external_reference": "homesteady-payment-123",
                "amount_minor": 2500,
                "currency": "USD",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(payment_intent_id)
    assert response.json()["merchant_id"] == str(merchant_id)
    assert response.json()["status"] == "requires_payment_method"

    assert received_arguments["merchant_id"] == merchant_id
    assert received_arguments["payment_intent_create"].model_dump() == {
        "customer_id": customer_id,
        "external_reference": "homesteady-payment-123",
        "amount_minor": 2500,
        "currency": "USD",
    }


def test_create_payment_intent_returns_not_found_for_invalid_customer(
    monkeypatch,
) -> None:
    """Return 404 when the customer is missing or owned by another merchant."""

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
        payment_intent_create,
    ):
        raise payment_intents.CustomerNotFoundError(
            payment_intent_create.customer_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "create_payment_intent",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/payment-intents",
            json={
                "customer_id": str(customer_id),
                "external_reference": "homesteady-payment-123",
                "amount_minor": 2500,
                "currency": "USD",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Customer not found.",
    }


def test_create_payment_intent_returns_conflict_for_duplicate_reference(
    monkeypatch,
) -> None:
    """Return 409 when a merchant reuses a payment-intent reference."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_duplicate(
        session,
        merchant_id,
        payment_intent_create,
    ):
        raise payment_intents.PaymentIntentAlreadyExistsError(
            payment_intent_create.external_reference,
        )

    monkeypatch.setattr(
        payment_intents,
        "create_payment_intent",
        raise_duplicate,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/payment-intents",
            json={
                "customer_id": str(customer_id),
                "external_reference": "homesteady-payment-123",
                "amount_minor": 2500,
                "currency": "USD",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "A payment intent with this external reference "
            "already exists for this merchant."
        ),
    }


def test_get_payment_intent_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Retrieve a payment intent within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_get_payment_intent(
        session,
        merchant_id,
        payment_intent_id,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        return payment_intent

    monkeypatch.setattr(
        payment_intents,
        "get_payment_intent",
        fake_get_payment_intent,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            f"/api/v1/payment-intents/{payment_intent_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(payment_intent_id)
    assert response.json()["merchant_id"] == str(merchant_id)

    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_intent_id": payment_intent_id,
    }


def test_get_payment_intent_returns_not_found(
    monkeypatch,
) -> None:
    """Return 404 when the payment intent is missing or merchant-inaccessible."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

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
        payment_intent_id,
    ):
        raise payment_intents.PaymentIntentNotFoundError(
            payment_intent_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "get_payment_intent",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            f"/api/v1/payment-intents/{payment_intent_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Payment intent not found.",
    }


def test_list_payment_intents_uses_authenticated_merchant_and_returns_empty_list(
    monkeypatch,
) -> None:
    """List payment intents within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    received_merchant_ids: list[uuid.UUID] = []

    def fake_list_payment_intents(session, merchant_id):
        received_merchant_ids.append(merchant_id)
        return []

    monkeypatch.setattr(
        payment_intents,
        "list_payment_intents",
        fake_list_payment_intents,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get("/api/v1/payment-intents")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    assert received_merchant_ids == [merchant_id]


def test_list_payment_intents_returns_serialized_records(
    monkeypatch,
) -> None:
    """Return merchant payment intents as PaymentIntentRead records."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        created_at=timestamp,
        updated_at=timestamp,
    )

    monkeypatch.setattr(
        payment_intents,
        "list_payment_intents",
        lambda session, merchant_id: [payment_intent],
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get("/api/v1/payment-intents")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(payment_intent.id),
            "merchant_id": str(merchant_id),
            "customer_id": str(customer_id),
            "payment_method_id": None,
            "external_reference": "homesteady-payment-123",
            "amount_minor": 2500,
            "currency": "USD",
            "status": "requires_payment_method",
            "last_error_code": None,
            "created_at": timestamp.isoformat().replace("+00:00", "Z"),
            "updated_at": timestamp.isoformat().replace("+00:00", "Z"),
        },
    ]


def test_confirm_payment_intent_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Confirm a payment intent within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="succeeded",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_confirm_payment_intent(
        session,
        merchant_id,
        payment_intent_id,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        return payment_intent

    monkeypatch.setattr(
        payment_intents,
        "confirm_payment_intent",
        fake_confirm_payment_intent,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/confirm",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(payment_intent_id)
    assert response.json()["status"] == "succeeded"

    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_intent_id": payment_intent_id,
    }


def test_confirm_payment_intent_returns_not_found(
    monkeypatch,
) -> None:
    """Return 404 when the payment intent is missing or merchant-inaccessible."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

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
        payment_intent_id,
    ):
        raise payment_intents.PaymentIntentNotFoundError(
            payment_intent_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "confirm_payment_intent",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/confirm",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Payment intent not found.",
    }


def test_confirm_payment_intent_returns_conflict_for_invalid_state(
    monkeypatch,
) -> None:
    """Return 409 when the payment intent cannot be confirmed."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_invalid_state(
        session,
        merchant_id,
        payment_intent_id,
    ):
        raise payment_intents.PaymentIntentInvalidStateError(
            "confirmed",
            "succeeded",
        )

    monkeypatch.setattr(
        payment_intents,
        "confirm_payment_intent",
        raise_invalid_state,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/confirm",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("Payment intent cannot be confirmed from status: succeeded."),
    }


def test_cancel_payment_intent_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Cancel a payment intent within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="canceled",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_cancel_payment_intent(
        session,
        merchant_id,
        payment_intent_id,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        return payment_intent

    monkeypatch.setattr(
        payment_intents,
        "cancel_payment_intent",
        fake_cancel_payment_intent,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/cancel",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(payment_intent_id)
    assert response.json()["status"] == "canceled"

    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_intent_id": payment_intent_id,
    }


def test_cancel_payment_intent_returns_not_found(
    monkeypatch,
) -> None:
    """Return 404 when the payment intent is missing or merchant-inaccessible."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

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
        payment_intent_id,
    ):
        raise payment_intents.PaymentIntentNotFoundError(
            payment_intent_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "cancel_payment_intent",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/cancel",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Payment intent not found.",
    }


def test_cancel_payment_intent_returns_conflict_for_invalid_state(
    monkeypatch,
) -> None:
    """Return 409 when the payment intent cannot be canceled."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_invalid_state(
        session,
        merchant_id,
        payment_intent_id,
    ):
        raise payment_intents.PaymentIntentInvalidStateError(
            "canceled",
            "succeeded",
        )

    monkeypatch.setattr(
        payment_intents,
        "cancel_payment_intent",
        raise_invalid_state,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/cancel",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("Payment intent cannot be canceled from status: succeeded."),
    }


def test_confirm_payment_intent_returns_controlled_decline(
    monkeypatch,
) -> None:
    """Return a retryable payment intent with its latest decline code."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-payment-decline",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        last_error_code="card_declined",
        created_at=timestamp,
        updated_at=timestamp,
    )

    monkeypatch.setattr(
        payment_intents,
        "confirm_payment_intent",
        lambda session, merchant_id, payment_intent_id: payment_intent,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/confirm",
            json={"test_scenario": "card_declined"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "requires_payment_method"
    assert response.json()["last_error_code"] == "card_declined"


def test_attach_payment_method_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Attach a payment method within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="homesteady-attached-payment-method",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_attach_payment_method(
        session,
        merchant_id,
        payment_intent_id,
        payment_method_id,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        received_arguments["payment_method_id"] = payment_method_id
        return payment_intent

    monkeypatch.setattr(
        payment_intents,
        "attach_payment_method",
        fake_attach_payment_method,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/attach-payment-method",
            json={
                "payment_method_id": str(payment_method_id),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(payment_intent_id)
    assert response.json()["payment_method_id"] == str(payment_method_id)

    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_intent_id": payment_intent_id,
        "payment_method_id": payment_method_id,
    }


def test_attach_payment_method_returns_not_found(
    monkeypatch,
) -> None:
    """Return 404 when the intent or payment method is not merchant-accessible."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

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
        payment_intent_id,
        payment_method_id,
    ):
        raise payment_intents.PaymentMethodNotFoundError(
            payment_method_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "attach_payment_method",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/attach-payment-method",
            json={
                "payment_method_id": str(payment_method_id),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Payment intent or payment method not found.",
    }


def test_attach_payment_method_returns_customer_mismatch_conflict(
    monkeypatch,
) -> None:
    """Return 409 when the payment method belongs to another customer."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_customer_mismatch(
        session,
        merchant_id,
        payment_intent_id,
        payment_method_id,
    ):
        raise payment_intents.PaymentMethodCustomerMismatchError(
            payment_method_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "attach_payment_method",
        raise_customer_mismatch,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/attach-payment-method",
            json={
                "payment_method_id": str(payment_method_id),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Payment method belongs to a different customer.",
    }


def test_attach_payment_method_returns_inactive_conflict(
    monkeypatch,
) -> None:
    """Return 409 when the payment method is inactive."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_inactive(
        session,
        merchant_id,
        payment_intent_id,
        payment_method_id,
    ):
        raise payment_intents.PaymentMethodInactiveError(
            payment_method_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "attach_payment_method",
        raise_inactive,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/attach-payment-method",
            json={
                "payment_method_id": str(payment_method_id),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Payment method is inactive.",
    }


def test_confirm_payment_intent_returns_inactive_method_conflict(
    monkeypatch,
) -> None:
    """Return 409 when the attached payment method is inactive."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_inactive(
        session,
        merchant_id,
        payment_intent_id,
    ):
        raise payment_intents.PaymentMethodInactiveError(
            uuid.uuid4(),
        )

    monkeypatch.setattr(
        payment_intents,
        "confirm_payment_intent",
        raise_inactive,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/confirm",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Attached payment method is inactive.",
    }


def test_confirm_payment_intent_returns_payment_method_required_conflict(
    monkeypatch,
) -> None:
    """Return 409 when confirmation has no attached payment method."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_payment_method_required(
        session,
        merchant_id,
        payment_intent_id,
    ):
        raise payment_intents.PaymentMethodRequiredError(
            payment_intent_id,
        )

    monkeypatch.setattr(
        payment_intents,
        "confirm_payment_intent",
        raise_payment_method_required,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/confirm",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Payment method must be attached before confirmation.",
    }


def test_confirm_payment_intent_does_not_pass_legacy_scenario(
    monkeypatch,
) -> None:
    """Confirm without forwarding a request-controlled test scenario."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        payment_method_id=payment_method_id,
        external_reference="homesteady-confirm-attached-method",
        amount_minor=2500,
        currency="USD",
        status="succeeded",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_confirm_payment_intent(
        session,
        merchant_id,
        payment_intent_id,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["payment_intent_id"] = payment_intent_id
        return payment_intent

    monkeypatch.setattr(
        payment_intents,
        "confirm_payment_intent",
        fake_confirm_payment_intent,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            f"/api/v1/payment-intents/{payment_intent_id}/confirm",
            json={
                "test_scenario": "card_declined",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"

    assert received_arguments == {
        "merchant_id": merchant_id,
        "payment_intent_id": payment_intent_id,
    }
