"""Pydantic schemas for merchant API operations."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MerchantCreate(BaseModel):
    """Request body for creating a merchant."""

    name: str = Field(
        min_length=1,
        max_length=200,
        examples=["Homesteady"],
    )


class MerchantRead(BaseModel):
    """Merchant data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
