"""Refund API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RefundCreate(BaseModel):
    """Request body for creating a refund."""

    payment_intent_id: uuid.UUID

    external_reference: str = Field(
        min_length=1,
        max_length=255,
        examples=["homesteady-refund-123"],
    )

    amount_minor: int = Field(
        gt=0,
        examples=[1000],
    )


class RefundRead(BaseModel):
    """Response body for a persisted refund."""

    model_config = {
        "from_attributes": True,
    }

    id: uuid.UUID
    merchant_id: uuid.UUID
    payment_intent_id: uuid.UUID
    external_reference: str
    amount_minor: int
    currency: str
    status: str
    created_at: datetime
