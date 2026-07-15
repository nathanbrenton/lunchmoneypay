"""Customer API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerRead
from app.services.customer import create_customer, get_customer
from app.services.exceptions import (
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_endpoint(
    customer_create: CustomerCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> Customer:
    """Create a customer for the authenticated merchant."""

    try:
        return create_customer(
            session=session,
            merchant_id=credential.merchant_id,
            customer_create=customer_create,
        )
    except CustomerAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A customer with this external reference "
                "already exists for this merchant."
            ),
        ) from exc


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
)
def get_customer_endpoint(
    customer_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> Customer:
    """Return a customer owned by the authenticated merchant."""

    try:
        return get_customer(
            session=session,
            merchant_id=credential.merchant_id,
            customer_id=customer_id,
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        ) from exc
