"""Tests for payment-intent service functions."""

import uuid
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.payment_intent import create_payment_intent


def test_create_payment_intent_uses_authenticated_merchant() -> None:
    """Create a payment intent for a customer owned by the merchant."""

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

    payment_intent_create = PaymentIntentCreate(
        customer_id=customer_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
    )

    result = create_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_create=payment_intent_create,
    )

    assert isinstance(result, PaymentIntent)
    assert result.merchant_id == merchant_id
    assert result.customer_id == customer_id
    assert result.external_reference == "homesteady-payment-123"
    assert result.amount_minor == 2500
    assert result.currency == "USD"

    session.get.assert_called_once_with(Customer, customer_id)
    session.add.assert_called_once_with(result)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(result)


def test_create_payment_intent_rejects_customer_owned_by_another_merchant() -> None:
    """Reject customers outside the authenticated merchant boundary."""

    import pytest

    from app.services.exceptions import CustomerNotFoundError

    session = MagicMock(spec=Session)
    authenticated_merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    customer = Customer(
        id=customer_id,
        merchant_id=uuid.uuid4(),
        external_reference="other-merchant-user",
        display_name="Other Merchant Customer",
        status="active",
    )

    session.get.return_value = customer

    with pytest.raises(CustomerNotFoundError):
        create_payment_intent(
            session=session,
            merchant_id=authenticated_merchant_id,
            payment_intent_create=PaymentIntentCreate(
                customer_id=customer_id,
                external_reference="homesteady-payment-123",
                amount_minor=2500,
                currency="USD",
            ),
        )

    session.add.assert_not_called()
    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_create_payment_intent_rejects_duplicate_external_reference() -> None:
    """Reject duplicate payment references within one merchant."""

    import pytest
    from sqlalchemy.exc import IntegrityError

    from app.services.exceptions import PaymentIntentAlreadyExistsError

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
    session.commit.side_effect = IntegrityError(
        statement=None,
        params=None,
        orig=Exception("duplicate payment reference"),
    )

    with pytest.raises(PaymentIntentAlreadyExistsError):
        create_payment_intent(
            session=session,
            merchant_id=merchant_id,
            payment_intent_create=PaymentIntentCreate(
                customer_id=customer_id,
                external_reference="homesteady-payment-123",
                amount_minor=2500,
                currency="USD",
            ),
        )

    session.rollback.assert_called_once_with()
    session.refresh.assert_not_called()
