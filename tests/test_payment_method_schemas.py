"""Tests for mock payment-method API schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodRead,
)


def test_payment_method_create_accepts_valid_card() -> None:
    """Accept a supported mock card and processing scenario."""

    payment_method = PaymentMethodCreate(
        customer_id=uuid.uuid4(),
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        test_scenario="success",
    )

    assert payment_method.card_brand == "visa"
    assert payment_method.card_last4 == "4242"
    assert payment_method.test_scenario == "success"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("card_last4", "424"),
        ("card_last4", "abcd"),
        ("card_exp_month", 0),
        ("card_exp_month", 13),
        ("card_exp_year", 1999),
        ("test_scenario", "insufficient_funds"),
    ],
)
def test_payment_method_create_rejects_invalid_fields(
    field: str,
    value: object,
) -> None:
    """Reject unsupported or malformed mock-card values."""

    payload = {
        "customer_id": uuid.uuid4(),
        "card_brand": "visa",
        "card_last4": "4242",
        "card_exp_month": 12,
        "card_exp_year": 2030,
        "test_scenario": "success",
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        PaymentMethodCreate(**payload)


def test_payment_method_read_accepts_expected_fields() -> None:
    """Serialize the stored mock payment-method representation."""

    timestamp = datetime.now(UTC)

    payment_method = PaymentMethodRead(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
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

    assert payment_method.type == "card"
    assert payment_method.status == "active"
