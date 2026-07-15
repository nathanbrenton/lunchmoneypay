"""Service operations for mock payment methods."""

import uuid

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import PaymentMethodCreate
from app.services.exceptions import CustomerNotFoundError


def create_payment_method(
    session: Session,
    merchant_id: uuid.UUID,
    payment_method_create: PaymentMethodCreate,
) -> PaymentMethod:
    """Create a mock card for a merchant-owned customer."""

    customer = session.get(
        Customer,
        payment_method_create.customer_id,
    )

    if customer is None or customer.merchant_id != merchant_id:
        raise CustomerNotFoundError(
            payment_method_create.customer_id,
        )

    payment_method = PaymentMethod(
        merchant_id=merchant_id,
        customer_id=payment_method_create.customer_id,
        type="card",
        card_brand=payment_method_create.card_brand,
        card_last4=payment_method_create.card_last4,
        card_exp_month=payment_method_create.card_exp_month,
        card_exp_year=payment_method_create.card_exp_year,
        test_scenario=payment_method_create.test_scenario,
    )

    session.add(payment_method)
    session.commit()
    session.refresh(payment_method)

    return payment_method
