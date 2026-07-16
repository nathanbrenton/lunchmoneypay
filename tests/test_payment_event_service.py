"""Tests for durable payment-event service operations."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.payment_event import PaymentEvent
from app.models.payment_intent import PaymentIntent
from app.services.exceptions import PaymentEventNotFoundError
from app.services.payment_event import (
    create_payment_event,
    get_payment_event,
    list_payment_events,
)


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


def test_get_payment_event_returns_merchant_owned_record() -> None:
    """Return a payment event owned by the authenticated merchant."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_event_id = uuid.uuid4()

    payment_event = PaymentEvent(
        id=payment_event_id,
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload={
            "status": "succeeded",
        },
    )

    session.get.return_value = payment_event

    result = get_payment_event(
        session=session,
        merchant_id=merchant_id,
        payment_event_id=payment_event_id,
    )

    assert result is payment_event
    session.get.assert_called_once_with(
        PaymentEvent,
        payment_event_id,
    )


def test_get_payment_event_rejects_other_merchant_record() -> None:
    """Hide payment events owned by another merchant."""

    session = MagicMock(spec=Session)
    authenticated_merchant_id = uuid.uuid4()
    other_merchant_id = uuid.uuid4()
    payment_event_id = uuid.uuid4()

    payment_event = PaymentEvent(
        id=payment_event_id,
        merchant_id=other_merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload={
            "status": "succeeded",
        },
    )

    session.get.return_value = payment_event

    with pytest.raises(PaymentEventNotFoundError):
        get_payment_event(
            session=session,
            merchant_id=authenticated_merchant_id,
            payment_event_id=payment_event_id,
        )

    session.get.assert_called_once_with(
        PaymentEvent,
        payment_event_id,
    )


def test_list_payment_events_filters_by_merchant_and_orders_newest_first() -> None:
    """List only the authenticated merchant's events, newest first."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()

    newest_event = PaymentEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload={"status": "succeeded"},
    )
    older_event = PaymentEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.payment_failed",
        payload={"status": "requires_payment_method"},
    )

    session.scalars.return_value.all.return_value = [
        newest_event,
        older_event,
    ]

    result = list_payment_events(
        session=session,
        merchant_id=merchant_id,
    )

    assert result == [
        newest_event,
        older_event,
    ]

    statement = session.scalars.call_args.args[0]
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "payment_events.merchant_id" in compiled
    assert merchant_id.hex in compiled
    assert "payment_events.created_at DESC" in compiled


def test_list_payment_events_returns_empty_list() -> None:
    """Return an empty list when a merchant has no payment events."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()

    session.scalars.return_value.all.return_value = []

    result = list_payment_events(
        session=session,
        merchant_id=merchant_id,
    )

    assert result == []
    session.scalars.assert_called_once()


def test_list_payment_events_filters_by_payment_intent() -> None:
    """List events for one merchant-owned payment intent."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    payment_event = PaymentEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        event_type="payment_intent.succeeded",
        payload={"status": "succeeded"},
    )

    session.scalars.return_value.all.return_value = [payment_event]

    result = list_payment_events(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result == [payment_event]

    statement = session.scalars.call_args.args[0]
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "payment_events.merchant_id" in compiled
    assert merchant_id.hex in compiled
    assert "payment_events.payment_intent_id" in compiled
    assert payment_intent_id.hex in compiled
    assert "payment_events.created_at DESC" in compiled


def test_list_payment_events_filters_by_event_type() -> None:
    """List only events matching the requested event type."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()

    payment_event = PaymentEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.payment_failed",
        payload={
            "status": "requires_payment_method",
            "last_error_code": "card_declined",
        },
    )

    session.scalars.return_value.all.return_value = [payment_event]

    result = list_payment_events(
        session=session,
        merchant_id=merchant_id,
        event_type="payment_intent.payment_failed",
    )

    assert result == [payment_event]

    statement = session.scalars.call_args.args[0]
    compiled = str(
        statement.compile(
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "payment_events.merchant_id" in compiled
    assert merchant_id.hex in compiled
    assert "payment_events.event_type" in compiled
    assert "payment_intent.payment_failed" in compiled
    assert "payment_events.created_at DESC" in compiled
