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
from app.services.idempotency import (
    create_idempotency_record,
    get_idempotency_record,
    hash_request_payload,
    validate_idempotency_replay,
)
from app.services.payment_event import create_refund_event
from app.services.payment_intent import get_payment_intent
from app.services.webhook import dispatch_payment_event_safely


def create_refund(
    session: Session,
    merchant_id: uuid.UUID,
    refund_create: RefundCreate,
    idempotency_key: str | None = None,
) -> Refund:
    """Create or replay a refund against a succeeded payment intent."""

    request_hash = hash_request_payload(refund_create)

    if idempotency_key is not None:
        existing_record = get_idempotency_record(
            session=session,
            merchant_id=merchant_id,
            idempotency_key=idempotency_key,
        )

        if existing_record is not None:
            validate_idempotency_replay(
                record=existing_record,
                operation="refund.create",
                request_hash=request_hash,
                resource_type="refund",
            )
            return get_refund(
                session=session,
                merchant_id=merchant_id,
                refund_id=existing_record.resource_id,
            )

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

    if idempotency_key is not None:
        session.add(
            create_idempotency_record(
                merchant_id=merchant_id,
                idempotency_key=idempotency_key,
                operation="refund.create",
                request_hash=request_hash,
                resource_type="refund",
                resource_id=refund.id,
            )
        )

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
