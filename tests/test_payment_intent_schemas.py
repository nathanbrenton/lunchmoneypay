"""Tests for payment-intent API schemas."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.payment_intent import PaymentIntentCreate


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

    from datetime import UTC, datetime

    from app.schemas.payment_intent import PaymentIntentRead

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
