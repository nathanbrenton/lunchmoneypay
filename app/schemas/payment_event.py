"""Payment-event API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PaymentEventRead(BaseModel):
    """Response body for a persisted payment event."""

    model_config = {
        "from_attributes": True,
    }

    id: uuid.UUID
    merchant_id: uuid.UUID
    payment_intent_id: uuid.UUID
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
