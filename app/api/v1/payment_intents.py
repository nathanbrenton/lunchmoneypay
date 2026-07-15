"""Payment-intent API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import (
    PaymentIntentConfirm,
    PaymentIntentCreate,
    PaymentIntentRead,
)
from app.services.exceptions import (
    CustomerNotFoundError,
    PaymentIntentAlreadyExistsError,
    PaymentIntentInvalidStateError,
    PaymentIntentNotFoundError,
)
from app.services.payment_intent import (
    cancel_payment_intent,
    confirm_payment_intent,
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


@router.post(
    "/{payment_intent_id}/cancel",
    response_model=PaymentIntentRead,
)
def cancel_payment_intent_endpoint(
    payment_intent_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> PaymentIntent:
    """Cancel an eligible payment intent for the authenticated merchant."""

    try:
        return cancel_payment_intent(
            session=session,
            merchant_id=credential.merchant_id,
            payment_intent_id=payment_intent_id,
        )
    except PaymentIntentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found.",
        ) from exc
    except PaymentIntentInvalidStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{payment_intent_id}/confirm",
    response_model=PaymentIntentRead,
)
def confirm_payment_intent_endpoint(
    payment_intent_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
    payment_intent_confirm: Annotated[
        PaymentIntentConfirm | None,
        Body(),
    ] = None,
) -> PaymentIntent:
    """Confirm an eligible payment intent for the authenticated merchant."""

    # An omitted body uses the normal successful mock scenario.
    confirmation = payment_intent_confirm or PaymentIntentConfirm()

    try:
        return confirm_payment_intent(
            session=session,
            merchant_id=credential.merchant_id,
            payment_intent_id=payment_intent_id,
            payment_intent_confirm=confirmation,
        )
    except PaymentIntentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found.",
        ) from exc
    except PaymentIntentInvalidStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
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
