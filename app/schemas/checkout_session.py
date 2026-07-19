"""Schemas for the bounded LunchMoneyPay demo checkout contract."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class DemoCheckoutSessionCreate(BaseModel):
    """Merchant request containing no cardholder or authentication data."""

    customer_external_reference: str = Field(min_length=1, max_length=255)
    customer_display_name: str = Field(min_length=1, max_length=200)
    customer_email: EmailStr
    external_reference: str = Field(min_length=1, max_length=255)
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    test_scenario: Literal["success", "card_declined"] = "success"


class DemoCheckoutPaymentMethodSummary(BaseModel):
    """Safe display-only payment-method metadata."""

    type: Literal["card"]
    brand: str = Field(min_length=1, max_length=30)
    last4: str = Field(pattern=r"^[0-9]{4}$")


class DemoCheckoutSessionRead(BaseModel):
    """Completed demo checkout response returned to a merchant."""

    checkout_session_id: uuid.UUID
    payment_intent_id: uuid.UUID
    status: Literal["succeeded", "failed"]
    last_error_code: str | None = None
    payment_method: DemoCheckoutPaymentMethodSummary
    created_at: datetime
    updated_at: datetime
