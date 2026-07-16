"""Refund API endpoints."""

import uuid

from fastapi import APIRouter, Header, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.refund import Refund
from app.schemas.refund import RefundCreate, RefundRead
from app.services.exceptions import (
    IdempotencyKeyConflictError,
    PaymentIntentNotFoundError,
    PaymentIntentNotRefundableError,
    RefundAlreadyExistsError,
    RefundAmountExceedsAvailableError,
    RefundNotFoundError,
)
from app.services.refund import (
    create_refund,
    get_refund,
    list_refunds,
)

router = APIRouter(
    prefix="/refunds",
    tags=["refunds"],
)


@router.post(
    "",
    response_model=RefundRead,
    status_code=status.HTTP_201_CREATED,
)
def create_refund_endpoint(
    refund_create: RefundCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
) -> Refund:
    """Create a refund for the authenticated merchant."""

    try:
        return create_refund(
            session=session,
            merchant_id=credential.merchant_id,
            refund_create=refund_create,
            idempotency_key=idempotency_key,
        )
    except IdempotencyKeyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key was already used for a different request.",
        ) from exc
    except PaymentIntentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found.",
        ) from exc
    except RefundAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A refund with this external reference "
                "already exists for this merchant."
            ),
        ) from exc
    except PaymentIntentNotRefundableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment intent is not refundable.",
        ) from exc
    except RefundAmountExceedsAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Refund amount exceeds the remaining refundable amount.",
        ) from exc


@router.get(
    "",
    response_model=list[RefundRead],
)
def list_refunds_endpoint(
    credential: AuthenticatedCredential,
    session: DatabaseSession,
    payment_intent_id: uuid.UUID | None = None,
) -> list[Refund]:
    """List refunds owned by the authenticated merchant."""

    return list_refunds(
        session=session,
        merchant_id=credential.merchant_id,
        payment_intent_id=payment_intent_id,
    )


@router.get(
    "/{refund_id}",
    response_model=RefundRead,
)
def get_refund_endpoint(
    refund_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> Refund:
    """Retrieve a refund owned by the authenticated merchant."""

    try:
        return get_refund(
            session=session,
            merchant_id=credential.merchant_id,
            refund_id=refund_id,
        )
    except RefundNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found.",
        ) from exc
