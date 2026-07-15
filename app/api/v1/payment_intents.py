"""Payment-intent API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import (
    PaymentIntentCreate,
    PaymentIntentRead,
)
from app.services.exceptions import (
    CustomerNotFoundError,
    PaymentIntentAlreadyExistsError,
    PaymentIntentNotFoundError,
)
from app.services.payment_intent import (
    create_payment_intent,
    get_payment_intent,
    list_payment_intents,
)

router = APIRouter(
    prefix="/payment-intents",
    tags=["payment-intents"],
)


@router.post(
    "",
    response_model=PaymentIntentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_intent_endpoint(
    payment_intent_create: PaymentIntentCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> PaymentIntent:
    """Create a payment intent for the authenticated merchant."""

    try:
        return create_payment_intent(
            session=session,
            merchant_id=credential.merchant_id,
            payment_intent_create=payment_intent_create,
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        ) from exc
    except PaymentIntentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A payment intent with this external reference "
                "already exists for this merchant."
            ),
        ) from exc


@router.get(
    "",
    response_model=list[PaymentIntentRead],
)
def list_payment_intents_endpoint(
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> list[PaymentIntent]:
    """Return payment intents owned by the authenticated merchant."""

    return list_payment_intents(
        session=session,
        merchant_id=credential.merchant_id,
    )


@router.get(
    "/{payment_intent_id}",
    response_model=PaymentIntentRead,
)
def get_payment_intent_endpoint(
    payment_intent_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> PaymentIntent:
    """Return a payment intent owned by the authenticated merchant."""

    try:
        return get_payment_intent(
            session=session,
            merchant_id=credential.merchant_id,
            payment_intent_id=payment_intent_id,
        )
    except PaymentIntentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found.",
        ) from exc
