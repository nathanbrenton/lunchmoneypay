"""Payment-intent service functions."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.exceptions import (
    CustomerNotFoundError,
    PaymentIntentAlreadyExistsError,
    PaymentIntentInvalidStateError,
    PaymentIntentNotFoundError,
    PaymentMethodCustomerMismatchError,
    PaymentMethodInactiveError,
    PaymentMethodRequiredError,
)
from app.services.payment_event import create_payment_event
from app.services.payment_method import get_payment_method
from app.services.webhook import dispatch_payment_event_safely


def create_payment_intent(
    session: Session,
    merchant_id: uuid.UUID,
    payment_intent_create: PaymentIntentCreate,
) -> PaymentIntent:
    """Create a payment intent for a merchant-owned customer."""

    customer = session.get(
        Customer,
        payment_intent_create.customer_id,
    )

    if customer is None or customer.merchant_id != merchant_id:
        raise CustomerNotFoundError(
            payment_intent_create.customer_id,
        )

    payment_intent = PaymentIntent(
        merchant_id=merchant_id,
        customer_id=payment_intent_create.customer_id,
        external_reference=payment_intent_create.external_reference,
        amount_minor=payment_intent_create.amount_minor,
        currency=payment_intent_create.currency,
    )

    session.add(payment_intent)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()

        raise PaymentIntentAlreadyExistsError(
            payment_intent_create.external_reference,
        ) from exc

    session.refresh(payment_intent)

    return payment_intent


def get_payment_intent(
    session: Session,
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID,
) -> PaymentIntent:
    """Return a payment intent owned by the specified merchant."""

    payment_intent = session.get(
        PaymentIntent,
        payment_intent_id,
    )

    if payment_intent is None or payment_intent.merchant_id != merchant_id:
        raise PaymentIntentNotFoundError(payment_intent_id)

    return payment_intent


def list_payment_intents(
    session: Session,
    merchant_id: uuid.UUID,
) -> list[PaymentIntent]:
    """Return payment intents owned by the specified merchant."""

    statement = (
        select(PaymentIntent)
        .where(PaymentIntent.merchant_id == merchant_id)
        .order_by(
            PaymentIntent.created_at,
            PaymentIntent.id,
        )
    )

    return list(session.scalars(statement))


def confirm_payment_intent(
    session: Session,
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID,
) -> PaymentIntent:
    """Confirm an eligible mock payment intent."""

    payment_intent = get_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    if payment_intent.status != "requires_payment_method":
        raise PaymentIntentInvalidStateError(
            "confirmed",
            payment_intent.status,
        )

    if payment_intent.payment_method_id is None:
        raise PaymentMethodRequiredError(payment_intent.id)

    payment_method = get_payment_method(
        session=session,
        merchant_id=merchant_id,
        payment_method_id=payment_intent.payment_method_id,
    )

    if payment_method.status != "active":
        raise PaymentMethodInactiveError(payment_method.id)

    test_scenario = payment_method.test_scenario

    if test_scenario == "card_declined":
        payment_intent.last_error_code = "card_declined"
    else:
        payment_intent.status = "succeeded"
        payment_intent.last_error_code = None

    if payment_intent.status == "succeeded":
        event_type = "payment_intent.succeeded"
    else:
        event_type = "payment_intent.payment_failed"

    payment_event = create_payment_event(
        session=session,
        payment_intent=payment_intent,
        event_type=event_type,
    )

    session.commit()
    session.refresh(payment_intent)

    if payment_event is not None:
        dispatch_payment_event_safely(
            session=session,
            payment_event=payment_event,
        )

    return payment_intent


def cancel_payment_intent(
    session: Session,
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID,
) -> PaymentIntent:
    """Cancel an eligible payment intent."""

    payment_intent = get_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    if payment_intent.status != "requires_payment_method":
        raise PaymentIntentInvalidStateError(
            "canceled",
            payment_intent.status,
        )

    payment_intent.status = "canceled"

    payment_event = create_payment_event(
        session=session,
        payment_intent=payment_intent,
        event_type="payment_intent.canceled",
    )

    session.commit()
    session.refresh(payment_intent)

    if payment_event is not None:
        dispatch_payment_event_safely(
            session=session,
            payment_event=payment_event,
        )

    return payment_intent


def attach_payment_method(
    session: Session,
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID,
    payment_method_id: uuid.UUID,
) -> PaymentIntent:
    """Attach a merchant-owned payment method to a payment intent."""

    payment_intent = get_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    payment_method = get_payment_method(
        session=session,
        merchant_id=merchant_id,
        payment_method_id=payment_method_id,
    )

    if payment_method.status != "active":
        raise PaymentMethodInactiveError(payment_method.id)

    if payment_method.customer_id != payment_intent.customer_id:
        raise PaymentMethodCustomerMismatchError(payment_method.id)

    payment_intent.payment_method_id = payment_method.id

    session.commit()
    session.refresh(payment_intent)

    return payment_intent
