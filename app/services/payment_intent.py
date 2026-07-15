"""Payment-intent service functions."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.exceptions import (
    CustomerNotFoundError,
    PaymentIntentAlreadyExistsError,
)


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
