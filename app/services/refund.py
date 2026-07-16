"""Refund service operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.refund import Refund
from app.schemas.refund import RefundCreate
from app.services.exceptions import (
    PaymentIntentNotRefundableError,
    RefundAlreadyExistsError,
    RefundAmountExceedsAvailableError,
    RefundNotFoundError,
)
from app.services.payment_event import create_refund_event
from app.services.payment_intent import get_payment_intent
from app.services.webhook import dispatch_payment_event_safely


def create_refund(
    session: Session,
    merchant_id: uuid.UUID,
    refund_create: RefundCreate,
) -> Refund:
    """Create a synchronous refund against a succeeded payment intent."""

    payment_intent = get_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=refund_create.payment_intent_id,
    )

    if payment_intent.status != "succeeded":
        raise PaymentIntentNotRefundableError(payment_intent.id)

    refunded_amount = session.scalar(
        select(
            func.coalesce(
                func.sum(Refund.amount_minor),
                0,
            )
        ).where(
            Refund.merchant_id == merchant_id,
            Refund.payment_intent_id == payment_intent.id,
            Refund.status == "succeeded",
        )
    )

    already_refunded = int(refunded_amount or 0)
    refundable_amount = payment_intent.amount_minor - already_refunded

    if refund_create.amount_minor > refundable_amount:
        raise RefundAmountExceedsAvailableError(
            refund_create.amount_minor,
        )

    refund = Refund(
        merchant_id=merchant_id,
        payment_intent_id=payment_intent.id,
        external_reference=refund_create.external_reference,
        amount_minor=refund_create.amount_minor,
        currency=payment_intent.currency,
        status="succeeded",
    )

    session.add(refund)
    session.flush()

    payment_event = create_refund_event(
        session=session,
        refund=refund,
        payment_intent=payment_intent,
    )

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()

        raise RefundAlreadyExistsError(
            refund_create.external_reference,
        ) from exc

    session.refresh(refund)

    if payment_event is not None:
        dispatch_payment_event_safely(
            session=session,
            payment_event=payment_event,
        )

    return refund


def get_refund(
    session: Session,
    merchant_id: uuid.UUID,
    refund_id: uuid.UUID,
) -> Refund:
    """Return a refund owned by the specified merchant."""

    refund = session.get(
        Refund,
        refund_id,
    )

    if refund is None or refund.merchant_id != merchant_id:
        raise RefundNotFoundError(refund_id)

    return refund


def list_refunds(
    session: Session,
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID | None = None,
) -> list[Refund]:
    """List merchant refunds, newest first."""

    statement = select(Refund).where(
        Refund.merchant_id == merchant_id,
    )

    if payment_intent_id is not None:
        statement = statement.where(
            Refund.payment_intent_id == payment_intent_id,
        )

    statement = statement.order_by(
        Refund.created_at.desc(),
        Refund.id.desc(),
    )

    return list(session.scalars(statement).all())
