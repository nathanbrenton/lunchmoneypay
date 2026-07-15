"""Pydantic schemas for mock payment methods."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethodCreate(BaseModel):
    """Fields accepted when creating a reusable mock card."""

    customer_id: uuid.UUID

    card_brand: str = Field(
        min_length=1,
        max_length=30,
        examples=["visa"],
    )

    card_last4: str = Field(
        pattern=r"^[0-9]{4}$",
        examples=["4242"],
    )

    card_exp_month: int = Field(
        ge=1,
        le=12,
        examples=[12],
    )

    card_exp_year: int = Field(
        ge=2000,
        le=9999,
        examples=[2030],
    )

    test_scenario: Literal[
        "success",
        "card_declined",
    ] = "success"


class PaymentMethodRead(BaseModel):
    """Stored mock payment-method representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID
    type: Literal["card"]
    card_brand: str
    card_last4: str
    card_exp_month: int
    card_exp_year: int
    status: Literal["active", "inactive"]
    test_scenario: Literal[
        "success",
        "card_declined",
    ]
    created_at: datetime
    updated_at: datetime
