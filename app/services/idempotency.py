"""Idempotent create-request helpers."""

import hashlib
import json
import uuid

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.idempotency_record import IdempotencyRecord
from app.services.exceptions import IdempotencyKeyConflictError


def hash_request_payload(payload: BaseModel) -> str:
    """Hash a canonical JSON representation of a validated request."""

    body = json.dumps(
        payload.model_dump(mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    ).encode()

    return hashlib.sha256(body).hexdigest()


def get_idempotency_record(
    session: Session,
    merchant_id: uuid.UUID,
    idempotency_key: str,
) -> IdempotencyRecord | None:
    """Return a merchant-scoped idempotency record when present."""

    statement = select(IdempotencyRecord).where(
        IdempotencyRecord.merchant_id == merchant_id,
        IdempotencyRecord.idempotency_key == idempotency_key,
    )

    return session.scalar(statement)


def validate_idempotency_replay(
    record: IdempotencyRecord,
    operation: str,
    request_hash: str,
    resource_type: str,
) -> None:
    """Reject reuse of a key for a different request or resource."""

    if (
        record.operation != operation
        or record.request_hash != request_hash
        or record.resource_type != resource_type
    ):
        raise IdempotencyKeyConflictError(record.idempotency_key)


def create_idempotency_record(
    merchant_id: uuid.UUID,
    idempotency_key: str,
    operation: str,
    request_hash: str,
    resource_type: str,
    resource_id: uuid.UUID,
) -> IdempotencyRecord:
    """Build a completed idempotency record for the current transaction."""

    return IdempotencyRecord(
        merchant_id=merchant_id,
        idempotency_key=idempotency_key,
        operation=operation,
        request_hash=request_hash,
        resource_type=resource_type,
        resource_id=resource_id,
    )
