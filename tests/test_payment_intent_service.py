"""Tests for payment-intent service functions."""

import uuid
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.payment_intent import (
    create_payment_intent,
    get_payment_intent,
    list_payment_intents,
)


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


def test_get_payment_intent_returns_merchant_owned_record() -> None:
    """Return a payment intent owned by the authenticated merchant."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    session.get.return_value = payment_intent

    result = get_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result is payment_intent
    session.get.assert_called_once_with(PaymentIntent, payment_intent_id)


def test_get_payment_intent_rejects_record_owned_by_another_merchant() -> None:
    """Hide payment intents outside the authenticated merchant boundary."""

    import pytest

    from app.services.exceptions import PaymentIntentNotFoundError

    session = MagicMock(spec=Session)
    authenticated_merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        external_reference="other-merchant-payment",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    session.get.return_value = payment_intent

    with pytest.raises(PaymentIntentNotFoundError):
        get_payment_intent(
            session=session,
            merchant_id=authenticated_merchant_id,
            payment_intent_id=payment_intent_id,
        )


def test_list_payment_intents_filters_by_merchant_and_orders_results() -> None:
    """List payment intents within the authenticated merchant boundary."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()

    expected_results = [
        PaymentIntent(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            customer_id=uuid.uuid4(),
            external_reference="homesteady-payment-001",
            amount_minor=2500,
            currency="USD",
            status="requires_payment_method",
        ),
        PaymentIntent(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            customer_id=uuid.uuid4(),
            external_reference="homesteady-payment-002",
            amount_minor=5000,
            currency="USD",
            status="requires_payment_method",
        ),
    ]

    session.scalars.return_value = expected_results

    result = list_payment_intents(
        session=session,
        merchant_id=merchant_id,
    )

    assert result == expected_results

    statement = session.scalars.call_args.args[0]
    compiled = str(statement)

    assert "payment_intents.merchant_id" in compiled
    assert "payment_intents.created_at" in compiled
    assert "payment_intents.id" in compiled


def test_list_payment_intents_returns_empty_list() -> None:
    """Return an empty list when the merchant has no payment intents."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()

    session.scalars.return_value = []

    result = list_payment_intents(
        session=session,
        merchant_id=merchant_id,
    )

    assert result == []
    session.scalars.assert_called_once()
