"""Schemas for authenticated merchant context."""

import uuid

from pydantic import BaseModel


class AuthenticatedMerchantContext(BaseModel):
    """Safe identity information for an authenticated API credential."""

    merchant_id: uuid.UUID
    credential_id: uuid.UUID
    key_prefix: str
