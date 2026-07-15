"""Business logic for customer operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.exceptions import (
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
)


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
            str(customer_create.email) if customer_create.email is not None else None
        ),
    )

    session.add(customer)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise CustomerAlreadyExistsError(customer_create.external_reference) from exc

    session.refresh(customer)

    return customer


def get_customer(
    session: Session,
    merchant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> Customer:
    """Return a customer owned by the specified merchant."""

    customer = session.get(Customer, customer_id)

    if customer is None or customer.merchant_id != merchant_id:
        raise CustomerNotFoundError(customer_id)

    return customer


def list_customers(
    session: Session,
    merchant_id: uuid.UUID,
) -> list[Customer]:
    """Return customers owned by the specified merchant."""

    statement = (
        select(Customer)
        .where(Customer.merchant_id == merchant_id)
        .order_by(Customer.created_at, Customer.id)
    )

    return list(session.scalars(statement))


def update_customer(
    session: Session,
    merchant_id: uuid.UUID,
    customer_id: uuid.UUID,
    customer_update: CustomerUpdate,
) -> Customer:
    """Update a customer owned by the specified merchant."""

    customer = get_customer(
        session=session,
        merchant_id=merchant_id,
        customer_id=customer_id,
    )

    update_data = customer_update.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        if field_name == "email" and field_value is not None:
            field_value = str(field_value)

        setattr(customer, field_name, field_value)

    session.commit()
    session.refresh(customer)

    return customer
