"""Tests for refund API schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.refund import RefundCreate, RefundRead


def test_refund_create_accepts_valid_fields() -> None:
    """Accept a payment intent, reference, and positive amount."""

    payment_intent_id = uuid.uuid4()

    result = RefundCreate(
        payment_intent_id=payment_intent_id,
        external_reference="refund-123",
        amount_minor=1000,
    )

    assert result.payment_intent_id == payment_intent_id
    assert result.amount_minor == 1000


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("external_reference", ""),
        ("amount_minor", 0),
        ("amount_minor", -1),
    ],
)
def test_refund_create_rejects_invalid_fields(
    field_name: str,
    field_value: object,
) -> None:
    """Reject invalid refund creation values."""

    payload = {
        "payment_intent_id": uuid.uuid4(),
        "external_reference": "refund-123",
        "amount_minor": 1000,
    }
    payload[field_name] = field_value

    with pytest.raises(ValidationError):
        RefundCreate(**payload)


def test_refund_read_accepts_persisted_fields() -> None:
    """Represent a persisted refund."""

    timestamp = datetime.now(UTC)

    result = RefundRead(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        payment_intent_id=uuid.uuid4(),
        external_reference="refund-123",
        amount_minor=1000,
        currency="USD",
        status="succeeded",
        created_at=timestamp,
    )

    assert result.status == "succeeded"
    assert result.currency == "USD"
