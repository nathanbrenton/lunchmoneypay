"""Tests for payment-intent service functions."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_intent import PaymentIntent
from app.models.payment_method import PaymentMethod
from app.schemas.payment_intent import (
    PaymentIntentCreate,
)
from app.services import payment_intent as payment_intent_service
from app.services.payment_intent import (
    cancel_payment_intent,
    confirm_payment_intent,
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


def test_confirm_payment_intent_marks_payment_as_succeeded() -> None:
    """Confirm successfully using the attached payment method scenario."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="homesteady-payment-123",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    result = confirm_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result is payment_intent
    assert result.status == "succeeded"
    assert result.last_error_code is None
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_confirm_payment_intent_rejects_invalid_status() -> None:
    """Reject confirmation after a payment intent leaves its initial state."""

    import pytest

    from app.services.exceptions import PaymentIntentInvalidStateError

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
        status="succeeded",
    )

    session.get.return_value = payment_intent

    with pytest.raises(PaymentIntentInvalidStateError):
        confirm_payment_intent(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent_id,
        )

    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_cancel_payment_intent_marks_payment_as_canceled() -> None:
    """Cancel an eligible payment intent."""

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

    result = cancel_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result is payment_intent
    assert payment_intent.status == "canceled"

    session.get.assert_called_once_with(
        PaymentIntent,
        payment_intent_id,
    )
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_cancel_payment_intent_rejects_invalid_status() -> None:
    """Reject cancellation after a payment intent leaves its initial state."""

    import pytest

    from app.services.exceptions import PaymentIntentInvalidStateError

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
        status="succeeded",
    )

    session.get.return_value = payment_intent

    with pytest.raises(PaymentIntentInvalidStateError):
        cancel_payment_intent(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent_id,
        )

    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_confirm_payment_intent_records_controlled_decline() -> None:
    """Record a decline using the attached payment method scenario."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="homesteady-payment-decline",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        last_error_code=None,
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4000",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="card_declined",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    result = confirm_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result is payment_intent
    assert result.status == "requires_payment_method"
    assert result.last_error_code == "card_declined"
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_confirm_payment_intent_clears_previous_error_on_success() -> None:
    """Clear the previous error when the attached method succeeds."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="homesteady-payment-retry",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        last_error_code="card_declined",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    result = confirm_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result is payment_intent
    assert result.status == "succeeded"
    assert result.last_error_code is None
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_confirm_payment_intent_uses_attached_success_scenario() -> None:
    """Use the success scenario stored on the attached payment method."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="ordinary-payment-reference",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        last_error_code=None,
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    result = confirm_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result.status == "succeeded"
    assert result.last_error_code is None
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_attach_payment_method_sets_compatible_method_on_intent() -> None:
    """Attach an active payment method for the same merchant and customer."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-attach-payment-method",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    result = payment_intent_service.attach_payment_method(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        payment_method_id=payment_method_id,
    )

    assert result is payment_intent
    assert result.payment_method_id == payment_method_id

    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_attach_payment_method_rejects_different_customer() -> None:
    """Reject a payment method owned by a different customer."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_customer_id = uuid.uuid4()
    payment_method_customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=payment_intent_customer_id,
        external_reference="homesteady-customer-mismatch",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=payment_method_customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="success",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    with pytest.raises(
        payment_intent_service.PaymentMethodCustomerMismatchError,
    ):
        payment_intent_service.attach_payment_method(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent_id,
            payment_method_id=payment_method_id,
        )

    assert payment_intent.payment_method_id is None
    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_attach_payment_method_rejects_inactive_method() -> None:
    """Reject attachment when the payment method is inactive."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        external_reference="homesteady-inactive-payment-method",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="inactive",
        test_scenario="success",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    with pytest.raises(
        payment_intent_service.PaymentMethodInactiveError,
    ):
        payment_intent_service.attach_payment_method(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent_id,
            payment_method_id=payment_method_id,
        )

    assert payment_intent.payment_method_id is None
    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_confirm_payment_intent_uses_attached_payment_method_scenario() -> None:
    """Use the attached payment method's stored test scenario."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="homesteady-attached-decline",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4000",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="card_declined",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    result = payment_intent_service.confirm_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result is payment_intent
    assert result.status == "requires_payment_method"
    assert result.last_error_code == "card_declined"

    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_confirm_payment_intent_uses_attached_decline_scenario() -> None:
    """Use the decline scenario stored on the attached payment method."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="homesteady-attached-method-precedence",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4000",
        card_exp_month=12,
        card_exp_year=2030,
        status="active",
        test_scenario="card_declined",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    result = payment_intent_service.confirm_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result is payment_intent
    assert result.status == "requires_payment_method"
    assert result.last_error_code == "card_declined"

    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(payment_intent)


def test_confirm_payment_intent_rejects_inactive_attached_method() -> None:
    """Reject confirmation when the attached payment method is inactive."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_method_id=payment_method_id,
        external_reference="homesteady-inactive-attached-method",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    payment_method = PaymentMethod(
        id=payment_method_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        type="card",
        card_brand="visa",
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2030,
        status="inactive",
        test_scenario="success",
    )

    session.get.side_effect = [
        payment_intent,
        payment_method,
    ]

    with pytest.raises(
        payment_intent_service.PaymentMethodInactiveError,
    ):
        payment_intent_service.confirm_payment_intent(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent_id,
        )

    assert payment_intent.status == "requires_payment_method"
    assert payment_intent.last_error_code is None
    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_confirm_payment_intent_requires_attached_payment_method() -> None:
    """Reject confirmation when no payment method is attached."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        payment_method_id=None,
        external_reference="homesteady-missing-payment-method",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
    )

    session.get.return_value = payment_intent

    with pytest.raises(
        payment_intent_service.PaymentMethodRequiredError,
    ):
        payment_intent_service.confirm_payment_intent(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent_id,
        )

    assert payment_intent.status == "requires_payment_method"
    assert payment_intent.last_error_code is None
    session.commit.assert_not_called()
    session.refresh.assert_not_called()
