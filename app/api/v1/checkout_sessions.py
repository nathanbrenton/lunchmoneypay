"""Development-only bounded checkout-session API."""

from fastapi import APIRouter, Header, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.core.config import get_settings
from app.schemas.checkout_session import (
    DemoCheckoutPaymentMethodSummary,
    DemoCheckoutSessionCreate,
    DemoCheckoutSessionRead,
)
from app.services.checkout_session import create_demo_checkout_session
from app.services.exceptions import (
    IdempotencyKeyConflictError,
    PaymentIntentAlreadyExistsError,
)

router = APIRouter(prefix="/checkout-sessions", tags=["checkout-sessions"])


@router.post(
    "",
    response_model=DemoCheckoutSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_checkout_session_endpoint(
    payload: DemoCheckoutSessionCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
    idempotency_key: str = Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=255,
    ),
) -> DemoCheckoutSessionRead:
    """Run one fixed demo checkout without receiving cardholder data."""

    settings = get_settings()
    if not settings.demo_checkout_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo checkout is disabled.",
        )

    try:
        result = create_demo_checkout_session(
            session=session,
            merchant_id=credential.merchant_id,
            payload=payload,
            idempotency_key=idempotency_key,
            expiration_year=settings.demo_checkout_expiration_year,
        )
    except IdempotencyKeyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key was already used for a different request.",
        ) from exc
    except PaymentIntentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment reference already exists.",
        ) from exc

    payment_intent = result.payment_intent
    payment_method = result.payment_method
    return DemoCheckoutSessionRead(
        checkout_session_id=payment_intent.id,
        payment_intent_id=payment_intent.id,
        status=("succeeded" if payment_intent.status == "succeeded" else "failed"),
        last_error_code=payment_intent.last_error_code,
        payment_method=DemoCheckoutPaymentMethodSummary(
            type="card",
            brand=payment_method.card_brand,
            last4=payment_method.card_last4,
        ),
        created_at=payment_intent.created_at,
        updated_at=payment_intent.updated_at,
    )
