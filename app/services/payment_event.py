"""Payment-event service operations."""

from sqlalchemy.orm import Session

from app.models.payment_event import PaymentEvent
from app.models.payment_intent import PaymentIntent


def create_payment_event(
    session: Session,
    payment_intent: PaymentIntent,
    event_type: str,
) -> PaymentEvent:
    """Persist a snapshot of a payment-intent lifecycle event."""

    event = PaymentEvent(
        merchant_id=payment_intent.merchant_id,
        payment_intent_id=payment_intent.id,
        event_type=event_type,
        payload={
            "id": str(payment_intent.id),
            "external_reference": payment_intent.external_reference,
            "amount_minor": payment_intent.amount_minor,
            "currency": payment_intent.currency,
            "status": payment_intent.status,
            "last_error_code": payment_intent.last_error_code,
        },
    )

    # The calling lifecycle operation owns the transaction commit.
    session.add(event)

    return event
