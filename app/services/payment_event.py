"""Payment-event service operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_event import PaymentEvent
from app.models.payment_intent import PaymentIntent
from app.models.refund import Refund
from app.services.exceptions import PaymentEventNotFoundError


def create_payment_event(
    session: Session,
    payment_intent: PaymentIntent,
    event_type: str,
) -> PaymentEvent:
    """Persist a safe snapshot of a payment-intent lifecycle event."""

    payload: dict[str, object] = {
        "id": str(payment_intent.id),
        "external_reference": payment_intent.external_reference,
        "amount_minor": payment_intent.amount_minor,
        "currency": payment_intent.currency,
        "status": payment_intent.status,
        "last_error_code": payment_intent.last_error_code,
    }
    method = getattr(payment_intent, "_event_payment_method_summary", None)
    if method is not None:
        payload["payment_method"] = method

    event = PaymentEvent(
        merchant_id=payment_intent.merchant_id,
        payment_intent_id=payment_intent.id,
        event_type=event_type,
        payload=payload,
    )

    # The calling lifecycle operation owns the transaction commit.
    session.add(event)
    return event


def get_payment_event(
    session: Session,
    merchant_id: uuid.UUID,
    payment_event_id: uuid.UUID,
) -> PaymentEvent:
    """Return a payment event owned by the specified merchant."""

    payment_event = session.get(PaymentEvent, payment_event_id)

    if payment_event is None or payment_event.merchant_id != merchant_id:
        raise PaymentEventNotFoundError(payment_event_id)

    return payment_event


def list_payment_events(
    session: Session,
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID | None = None,
    event_type: str | None = None,
) -> list[PaymentEvent]:
    """List a merchant's payment events, newest first."""

    statement = select(PaymentEvent).where(
        PaymentEvent.merchant_id == merchant_id,
    )

    if payment_intent_id is not None:
        statement = statement.where(
            PaymentEvent.payment_intent_id == payment_intent_id,
        )

    if event_type is not None:
        statement = statement.where(PaymentEvent.event_type == event_type)

    statement = statement.order_by(PaymentEvent.created_at.desc())
    return list(session.scalars(statement).all())


def create_refund_event(
    session: Session,
    refund: Refund,
    payment_intent: PaymentIntent,
) -> PaymentEvent:
    """Add a refund snapshot to the current transaction."""

    event = PaymentEvent(
        merchant_id=refund.merchant_id,
        payment_intent_id=payment_intent.id,
        event_type="refund.succeeded",
        payload={
            "id": str(refund.id),
            "payment_intent_id": str(payment_intent.id),
            "external_reference": refund.external_reference,
            "amount_minor": refund.amount_minor,
            "currency": refund.currency,
            "status": refund.status,
        },
    )
    session.add(event)
    return event
