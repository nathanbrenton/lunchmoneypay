"""Payment-intent API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PaymentIntentCreate(BaseModel):
    """Request body for creating a payment intent."""

    customer_id: uuid.UUID

    external_reference: str = Field(
        min_length=1,
        max_length=255,
        examples=["homesteady-payment-123"],
    )

    amount_minor: int = Field(
        gt=0,
        examples=[2500],
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
        pattern="^[A-Z]{3}$",
        examples=["USD"],
    )


class PaymentIntentRead(BaseModel):
    """Response body for a persisted payment intent."""

    model_config = {
        "from_attributes": True,
    }

    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID
    external_reference: str
    amount_minor: int
    currency: str
    status: str
    last_error_code: str | None = None
    created_at: datetime
    updated_at: datetime


class PaymentIntentConfirm(BaseModel):
    """Request body for confirming a mock payment intent."""

    test_scenario: str = Field(
        default="success",
        pattern="^(success|card_declined)$",
        examples=["success"],
    )
