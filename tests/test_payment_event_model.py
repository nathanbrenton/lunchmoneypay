"""Tests for durable payment-event records."""

import uuid

from app.models.payment_event import PaymentEvent


def test_payment_event_uses_expected_table_name() -> None:
    """Store payment lifecycle events in a dedicated table."""

    assert PaymentEvent.__tablename__ == "payment_events"


def test_payment_event_has_required_identity_fields() -> None:
    """Associate each event with its merchant and payment intent."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    event = PaymentEvent(
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        event_type="payment_intent.succeeded",
    )

    assert event.merchant_id == merchant_id
    assert event.payment_intent_id == payment_intent_id
    assert event.event_type == "payment_intent.succeeded"


def test_payment_event_has_structured_payload() -> None:
    """Store event-specific details in a structured JSON payload."""

    payload = {
        "status": "succeeded",
        "amount_minor": 2500,
        "currency": "USD",
    }

    event = PaymentEvent(
        merchant_id=uuid.uuid4(),
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload=payload,
    )

    assert event.payload == payload

    column = PaymentEvent.__table__.c.payload

    assert column.nullable is False


def test_payment_event_has_supported_event_type_constraint() -> None:
    """Restrict events to supported payment-intent lifecycle types."""

    constraint = next(
        constraint
        for constraint in PaymentEvent.__table__.constraints
        if constraint.name == "ck_payment_events_event_type"
    )

    sql_text = str(constraint.sqltext)

    assert "payment_intent.succeeded" in sql_text
    assert "payment_intent.payment_failed" in sql_text
    assert "payment_intent.canceled" in sql_text


def test_payment_event_supports_refund_success() -> None:
    """Allow durable successful-refund lifecycle events."""

    constraint = next(
        constraint
        for constraint in PaymentEvent.__table__.constraints
        if constraint.name == "ck_payment_events_event_type"
    )

    assert "refund.succeeded" in str(constraint.sqltext)
