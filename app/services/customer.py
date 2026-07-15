"""Business logic for customer operations."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate
from app.services.exceptions import CustomerAlreadyExistsError


def create_customer(
    session: Session,
    merchant_id: uuid.UUID,
    customer_create: CustomerCreate,
) -> Customer:
    """Create and persist a customer owned by a merchant."""

    customer = Customer(
        merchant_id=merchant_id,
        external_reference=customer_create.external_reference,
        display_name=customer_create.display_name,
        email=(
            str(customer_create.email)
            if customer_create.email is not None
            else None
        ),
    )

    session.add(customer)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise CustomerAlreadyExistsError(
            customer_create.external_reference
        ) from exc

    session.refresh(customer)

    return customer
