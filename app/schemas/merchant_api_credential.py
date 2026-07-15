"""Pydantic schemas for merchant API credentials."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MerchantApiCredentialRead(BaseModel):
    """Stored merchant API credential metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    key_prefix: str
    status: str
    expires_at: datetime | None
    created_at: datetime


class MerchantApiCredentialCreated(MerchantApiCredentialRead):
    """Credential creation response containing the one-time API key."""

    api_key: str
