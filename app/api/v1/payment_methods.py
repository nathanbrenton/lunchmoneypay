"""Payment-method API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodRead,
)
from app.services.exceptions import (
    CustomerNotFoundError,
    PaymentMethodNotFoundError,
)
from app.services.payment_method import (
    create_payment_method,
    get_payment_method,
    list_payment_methods,
)

router = APIRouter(
    prefix="/payment-methods",
    tags=["payment-methods"],
)


@router.post(
    "",
    response_model=PaymentMethodRead,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_method_endpoint(
    payment_method_create: PaymentMethodCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> PaymentMethod:
    """Create a mock card for the authenticated merchant."""

    try:
        return create_payment_method(
            session=session,
            merchant_id=credential.merchant_id,
            payment_method_create=payment_method_create,
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        ) from exc


@router.get(
    "/{payment_method_id}",
    response_model=PaymentMethodRead,
)
def get_payment_method_endpoint(
    payment_method_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> PaymentMethod:
    """Retrieve a payment method owned by the authenticated merchant."""

    try:
        return get_payment_method(
            session=session,
            merchant_id=credential.merchant_id,
            payment_method_id=payment_method_id,
        )
    except PaymentMethodNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found.",
        ) from exc


@router.get(
    "",
    response_model=list[PaymentMethodRead],
)
def list_payment_methods_endpoint(
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> list[PaymentMethod]:
    """List payment methods owned by the authenticated merchant."""

    return list_payment_methods(
        session=session,
        merchant_id=credential.merchant_id,
    )
