"""Payment-intent API endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import (
    PaymentIntentCreate,
    PaymentIntentRead,
)
from app.services.exceptions import (
    CustomerNotFoundError,
    PaymentIntentAlreadyExistsError,
)
from app.services.payment_intent import create_payment_intent

router = APIRouter(
    prefix="/payment-intents",
    tags=["payment-intents"],
)


@router.post(
    "",
    response_model=PaymentIntentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_intent_endpoint(
    payment_intent_create: PaymentIntentCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> PaymentIntent:
    """Create a payment intent for the authenticated merchant."""

    try:
        return create_payment_intent(
            session=session,
            merchant_id=credential.merchant_id,
            payment_intent_create=payment_intent_create,
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        ) from exc
    except PaymentIntentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A payment intent with this external reference "
                "already exists for this merchant."
            ),
        ) from exc
