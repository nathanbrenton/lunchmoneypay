"""Webhook API schemas."""

import uuid
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, Field


class WebhookEndpointCreate(BaseModel):
    """Request body for registering a webhook destination."""

    url: AnyHttpUrl
    signing_secret: str = Field(min_length=32, max_length=255)


class WebhookEndpointRead(BaseModel):
    """Response body for a persisted webhook destination."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    merchant_id: uuid.UUID
    url: str
    status: str
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryRead(BaseModel):
    """Response body for a webhook-delivery attempt."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    merchant_id: uuid.UUID
    webhook_endpoint_id: uuid.UUID
    payment_event_id: uuid.UUID
    status: str
    response_status: int | None = None
    error_message: str | None = None
    attempted_at: datetime
