"""Tests for mock payment-method service operations."""

import uuid
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import PaymentMethodCreate
from app.services.payment_method import create_payment_method


def test_create_payment_method_uses_authenticated_merchant() -> None:
    """Create a mock card for a customer owned by the merchant."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        status="active",
    )

    session.get.return_value = customer

    payload = PaymentMethodCreate(
        customer_id=customer_id,
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        test_scenario="success",
    )

    result = create_payment_method(
        session=session,
        merchant_id=merchant_id,
        payment_method_create=payload,
    )

    assert isinstance(result, PaymentMethod)
    assert result.merchant_id == merchant_id
    assert result.customer_id == customer_id
    assert result.type == "card"
    assert result.card_brand == "visa"
    assert result.card_last4 == "4242"
    assert result.test_scenario == "success"

    session.add.assert_called_once_with(result)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(result)
