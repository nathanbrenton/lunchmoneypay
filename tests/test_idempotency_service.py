"""Tests for idempotency helper behavior."""

import uuid

import pytest

from app.models.idempotency_record import IdempotencyRecord
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.exceptions import IdempotencyKeyConflictError
from app.services.idempotency import (
    hash_request_payload,
    validate_idempotency_replay,
)


def test_request_hash_is_stable_for_validated_payload() -> None:
    """Produce the same digest for the same validated request."""

    payload = PaymentIntentCreate(
        customer_id=uuid.uuid4(),
        external_reference="payment-123",
        amount_minor=2500,
        currency="USD",
    )

    assert hash_request_payload(payload) == hash_request_payload(payload)


def test_replay_rejects_different_request_hash() -> None:
    """Reject reuse of a key for different request content."""

    record = IdempotencyRecord(
        merchant_id=uuid.uuid4(),
        idempotency_key="create-payment-123",
        operation="payment_intent.create",
        request_hash="a" * 64,
        resource_type="payment_intent",
        resource_id=uuid.uuid4(),
    )

    with pytest.raises(IdempotencyKeyConflictError):
        validate_idempotency_replay(
            record=record,
            operation="payment_intent.create",
            request_hash="b" * 64,
            resource_type="payment_intent",
        )
