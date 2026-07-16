"""Tests for payment-intent API schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate, PaymentIntentRead


def test_payment_intent_create_accepts_valid_fields() -> None:
    """Accept the fields required to create a payment intent."""

    customer_id = uuid.uuid4()

    payment_intent = PaymentIntentCreate(
        customer_id=customer_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
    )

    assert payment_intent.customer_id == customer_id
    assert payment_intent.external_reference == "homesteady-payment-123"
    assert payment_intent.amount_minor == 2500
    assert payment_intent.currency == "USD"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("external_reference", ""),
        ("amount_minor", 0),
        ("amount_minor", -1),
        ("currency", "usd"),
        ("currency", "US"),
        ("currency", "USDD"),
    ],
)
def test_payment_intent_create_rejects_invalid_fields(
    field_name: str,
    field_value: object,
) -> None:
    """Reject invalid payment-intent creation values."""

    payload = {
        "customer_id": uuid.uuid4(),
        "external_reference": "homesteady-payment-123",
        "amount_minor": 2500,
        "currency": "USD",
    }

    payload[field_name] = field_value

    with pytest.raises(ValidationError):
        PaymentIntentCreate(**payload)


def test_payment_intent_read_accepts_expected_fields() -> None:
    """Represent a persisted payment intent in API responses."""

    payment_intent_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    payment_intent = PaymentIntentRead(
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

    assert payment_intent.id == payment_intent_id
    assert payment_intent.merchant_id == merchant_id
    assert payment_intent.customer_id == customer_id
    assert payment_intent.status == "requires_payment_method"


def test_payment_intent_read_accepts_optional_last_error_code() -> None:
    """Represent the latest mock processing error in API responses."""

    timestamp = datetime.now(UTC)

    payment_intent = PaymentIntentRead(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        last_error_code="card_declined",
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert payment_intent.last_error_code == "card_declined"


def test_payment_intent_confirm_accepts_supported_scenarios() -> None:
    """Accept explicit mock processing scenarios."""

    from app.schemas.payment_intent import PaymentIntentConfirm

    success = PaymentIntentConfirm(
        test_scenario="success",
    )
    decline = PaymentIntentConfirm(
        test_scenario="card_declined",
    )

    assert success.test_scenario == "success"
    assert decline.test_scenario == "card_declined"


def test_payment_intent_confirm_defaults_to_success() -> None:
    """Default confirmation to the successful mock scenario."""

    from app.schemas.payment_intent import PaymentIntentConfirm

    confirmation = PaymentIntentConfirm()

    assert confirmation.test_scenario == "success"


def test_payment_intent_confirm_rejects_unknown_scenario() -> None:
    """Reject unsupported mock processing scenarios."""

    from app.schemas.payment_intent import PaymentIntentConfirm

    with pytest.raises(ValidationError):
        PaymentIntentConfirm(
            test_scenario="insufficient_funds",
        )


def test_payment_intent_read_includes_optional_payment_method_id() -> None:
    """Serialize the payment method attached to a payment intent."""

    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        payment_method_id=payment_method_id,
        external_reference="homesteady-attached-method",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    result = PaymentIntentRead.model_validate(payment_intent)

    assert result.payment_method_id == payment_method_id
    assert result.model_dump()["payment_method_id"] == payment_method_id


def test_payment_intent_attach_accepts_payment_method_id() -> None:
    """Accept the payment method selected for attachment."""

    from app.schemas.payment_intent import PaymentIntentAttach

    payment_method_id = uuid.uuid4()

    attachment = PaymentIntentAttach(
        payment_method_id=payment_method_id,
    )

    assert attachment.payment_method_id == payment_method_id
