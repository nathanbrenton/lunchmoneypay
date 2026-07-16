"""Payment-event API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.payment_event import PaymentEvent
from app.schemas.payment_event import PaymentEventRead
from app.services.exceptions import PaymentEventNotFoundError
from app.services.payment_event import (
    get_payment_event,
    list_payment_events,
)

router = APIRouter(
    prefix="/payment-events",
    tags=["payment-events"],
)


@router.get(
    "/{payment_event_id}",
    response_model=PaymentEventRead,
)
def get_payment_event_endpoint(
    payment_event_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> PaymentEvent:
    """Retrieve a payment event owned by the authenticated merchant."""

    try:
        return get_payment_event(
            session=session,
            merchant_id=credential.merchant_id,
            payment_event_id=payment_event_id,
        )
    except PaymentEventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment event not found.",
        ) from exc


@router.get(
    "",
    response_model=list[PaymentEventRead],
)
def list_payment_events_endpoint(
    credential: AuthenticatedCredential,
    session: DatabaseSession,
    payment_intent_id: uuid.UUID | None = None,
    event_type: str | None = None,
) -> list[PaymentEvent]:
    """List payment events owned by the authenticated merchant."""

    return list_payment_events(
        session=session,
        merchant_id=credential.merchant_id,
        payment_intent_id=payment_intent_id,
        event_type=event_type,
    )
