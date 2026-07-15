"""Pydantic schemas for customer API operations."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    """Request body for creating a merchant-owned customer."""

    external_reference: str = Field(
        min_length=1,
        max_length=255,
        examples=["homesteady-user-123"],
    )

    display_name: str = Field(
        min_length=1,
        max_length=200,
        examples=["Example Customer"],
    )

    email: EmailStr | None = None


class CustomerRead(BaseModel):
    """Customer data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    external_reference: str
    display_name: str
    email: str | None
    status: str
    created_at: datetime
    updated_at: datetime
