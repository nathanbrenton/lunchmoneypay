"""Tests for durable payment-event service operations."""

import uuid
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.payment_event import PaymentEvent
from app.models.payment_intent import PaymentIntent
from app.services.payment_event import create_payment_event


def test_create_payment_event_records_payment_intent_snapshot() -> None:
    """Create a merchant-scoped event with a payment-intent snapshot."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        external_reference="homesteady-event-success",
        amount_minor=2500,
        currency="USD",
        status="succeeded",
        last_error_code=None,
    )

    result = create_payment_event(
        session=session,
        payment_intent=payment_intent,
        event_type="payment_intent.succeeded",
    )

    added_event = session.add.call_args.args[0]

    assert isinstance(added_event, PaymentEvent)
    assert result is added_event
    assert added_event.merchant_id == merchant_id
    assert added_event.payment_intent_id == payment_intent_id
    assert added_event.event_type == "payment_intent.succeeded"
    assert added_event.payload == {
        "id": str(payment_intent_id),
        "external_reference": "homesteady-event-success",
        "amount_minor": 2500,
        "currency": "USD",
        "status": "succeeded",
        "last_error_code": None,
    }

    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_create_payment_event_records_failed_payment_snapshot() -> None:
    """Record a retryable failed-payment event with its error code."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        external_reference="homesteady-event-decline",
        amount_minor=2500,
        currency="USD",
        status="requires_payment_method",
        last_error_code="card_declined",
    )

    result = create_payment_event(
        session=session,
        payment_intent=payment_intent,
        event_type="payment_intent.payment_failed",
    )

    assert result.event_type == "payment_intent.payment_failed"
    assert result.payload["status"] == "requires_payment_method"
    assert result.payload["last_error_code"] == "card_declined"

    session.add.assert_called_once_with(result)
    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_create_payment_event_records_canceled_payment_snapshot() -> None:
    """Record a canceled payment intent snapshot."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        external_reference="homesteady-event-canceled",
        amount_minor=2500,
        currency="USD",
        status="canceled",
        last_error_code=None,
    )

    result = create_payment_event(
        session=session,
        payment_intent=payment_intent,
        event_type="payment_intent.canceled",
    )

    assert result.event_type == "payment_intent.canceled"
    assert result.payload["status"] == "canceled"
    assert result.payload["last_error_code"] is None

    session.add.assert_called_once_with(result)
    session.commit.assert_not_called()
    session.refresh.assert_not_called()
