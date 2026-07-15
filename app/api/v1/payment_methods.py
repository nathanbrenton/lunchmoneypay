"""Payment-method API endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodRead,
)
from app.services.exceptions import CustomerNotFoundError
from app.services.payment_method import create_payment_method

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
