"""Tests for mock payment-method service operations."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import PaymentMethodCreate
from app.services.exceptions import PaymentMethodNotFoundError
from app.services.payment_method import (
    create_payment_method,
    deactivate_payment_method,
    get_payment_method,
    list_payment_methods,
)


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


def test_get_payment_method_returns_merchant_owned_record() -> None:
    """Return a payment method owned by the authenticated merchant."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.return_value = payment_method

    result = get_payment_method(
        session=session,
        merchant_id=merchant_id,
        payment_method_id=payment_method_id,
    )

    assert result is payment_method
    session.get.assert_called_once_with(PaymentMethod, payment_method_id)


def test_get_payment_method_rejects_other_merchant_record() -> None:
    """Hide payment methods owned by another merchant."""

    session = MagicMock(spec=Session)
    authenticated_merchant_id = uuid.uuid4()
    other_merchant_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=other_merchant_id,
        customer_id=uuid.uuid4(),
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.return_value = payment_method

    with pytest.raises(PaymentMethodNotFoundError):
        get_payment_method(
            session=session,
            merchant_id=authenticated_merchant_id,
            payment_method_id=payment_method_id,
        )

    session.get.assert_called_once_with(PaymentMethod, payment_method_id)


def test_list_payment_methods_filters_by_merchant_and_orders_results() -> None:
    """List payment methods within the authenticated merchant boundary."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()

    expected_results = [
        PaymentMethod(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            customer_id=uuid.uuid4(),
            type="card",
            card_brand="visa",
            card_last4="4242",
            card_exp_month=12,
            card_exp_year=2030,
            status="active",
            test_scenario="success",
        ),
        PaymentMethod(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            customer_id=uuid.uuid4(),
            type="card",
            card_brand="mastercard",
            card_last4="4444",
            card_exp_month=6,
            card_exp_year=2031,
            status="active",
            test_scenario="card_declined",
        ),
    ]

    session.scalars.return_value = expected_results

    result = list_payment_methods(
        session=session,
        merchant_id=merchant_id,
    )

    assert result == expected_results

    statement = session.scalars.call_args.args[0]
    compiled = str(statement)

    assert "payment_methods.merchant_id" in compiled
    assert "payment_methods.created_at" in compiled
    assert "payment_methods.id" in compiled


def test_deactivate_payment_method_marks_merchant_owned_record_inactive() -> None:
    """Deactivate a payment method owned by the authenticated merchant."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.return_value = payment_method

    result = deactivate_payment_method(
        session=session,
        merchant_id=merchant_id,
        payment_method_id=payment_method_id,
    )

    assert result is payment_method
    assert result.status == "inactive"

    session.get.assert_called_once_with(
        PaymentMethod,
        payment_method_id,
    )
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_method)


def test_deactivate_payment_method_rejects_other_merchant_record() -> None:
    """Reject deactivation of a payment method owned by another merchant."""

    session = MagicMock(spec=Session)
    authenticated_merchant_id = uuid.uuid4()
    other_merchant_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=other_merchant_id,
        customer_id=uuid.uuid4(),
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.return_value = payment_method

    with pytest.raises(PaymentMethodNotFoundError):
        deactivate_payment_method(
            session=session,
            merchant_id=authenticated_merchant_id,
            payment_method_id=payment_method_id,
        )

    session.commit.assert_not_called()
    session.refresh.assert_not_called()
