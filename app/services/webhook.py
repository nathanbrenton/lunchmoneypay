"""Webhook registration, signing, and delivery operations."""

import hashlib
import hmac
import json
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment_event import PaymentEvent
from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_endpoint import WebhookEndpoint
from app.schemas.webhook import WebhookEndpointCreate
from app.services.exceptions import (
    WebhookDeliveryNotFoundError,
    WebhookDeliveryNotRetryableError,
    WebhookEndpointAlreadyExistsError,
    WebhookEndpointNotFoundError,
)
from app.services.payment_event import get_payment_event


def _validated_webhook_url(value: str) -> str:
    """Fail closed if persisted endpoint data bypasses request-schema validation."""
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Webhook endpoint must be an absolute HTTP(S) URL.")
    return value


def create_webhook_endpoint(
    session: Session,
    merchant_id: uuid.UUID,
    endpoint_create: WebhookEndpointCreate,
) -> WebhookEndpoint:
    """Register a webhook endpoint for a merchant."""

    endpoint = WebhookEndpoint(
        merchant_id=merchant_id,
        url=str(endpoint_create.url),
        signing_secret=endpoint_create.signing_secret,
        status="active",
    )
    session.add(endpoint)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise WebhookEndpointAlreadyExistsError(endpoint.url) from exc

    session.refresh(endpoint)
    return endpoint


def get_webhook_endpoint(
    session: Session,
    merchant_id: uuid.UUID,
    webhook_endpoint_id: uuid.UUID,
) -> WebhookEndpoint:
    """Return a webhook endpoint owned by the merchant."""

    endpoint = session.get(WebhookEndpoint, webhook_endpoint_id)

    if endpoint is None or endpoint.merchant_id != merchant_id:
        raise WebhookEndpointNotFoundError(webhook_endpoint_id)

    return endpoint


def list_webhook_endpoints(
    session: Session,
    merchant_id: uuid.UUID,
) -> list[WebhookEndpoint]:
    """List a merchant's webhook endpoints."""

    statement = (
        select(WebhookEndpoint)
        .where(WebhookEndpoint.merchant_id == merchant_id)
        .order_by(WebhookEndpoint.created_at, WebhookEndpoint.id)
    )
    return list(session.scalars(statement).all())


def deactivate_webhook_endpoint(
    session: Session,
    merchant_id: uuid.UUID,
    webhook_endpoint_id: uuid.UUID,
) -> WebhookEndpoint:
    """Deactivate a merchant-owned webhook endpoint."""

    endpoint = get_webhook_endpoint(
        session=session,
        merchant_id=merchant_id,
        webhook_endpoint_id=webhook_endpoint_id,
    )
    endpoint.status = "inactive"
    session.commit()
    session.refresh(endpoint)
    return endpoint


def create_webhook_signature(
    signing_secret: str,
    timestamp: int,
    payload_body: bytes,
) -> str:
    """Create a timestamped HMAC-SHA256 signature header."""

    signed_payload = str(timestamp).encode() + b"." + payload_body
    digest = hmac.new(
        signing_secret.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def serialize_payment_event(payment_event: PaymentEvent) -> bytes:
    """Serialize a stable outbound webhook payload."""

    payload = {
        "id": str(payment_event.id),
        "type": payment_event.event_type,
        "created_at": payment_event.created_at.isoformat(),
        "data": payment_event.payload,
    }
    return json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _deliver_to_endpoint(
    session: Session,
    payment_event: PaymentEvent,
    endpoint: WebhookEndpoint,
    *,
    timeout_seconds: float,
) -> WebhookDelivery:
    """Attempt one signed delivery and add its result to the session."""

    payload_body = serialize_payment_event(payment_event)
    timestamp = int(time.time())
    signature = create_webhook_signature(
        endpoint.signing_secret,
        timestamp,
        payload_body,
    )
    request = Request(
        _validated_webhook_url(endpoint.url),
        data=payload_body,
        headers={
            "Content-Type": "application/json",
            "LunchMoneyPay-Event-Id": str(payment_event.id),
            "LunchMoneyPay-Signature": signature,
        },
        method="POST",
    )

    response_status = None
    error_message = None

    try:
        # The persisted URL is revalidated above as HTTP(S) before dispatch.
        with urlopen(  # nosec B310
            request,
            timeout=timeout_seconds,
        ) as response:
            response_status = response.status
            delivery_status = "succeeded" if 200 <= response.status < 300 else "failed"
    except HTTPError as exc:
        response_status = exc.code
        delivery_status = "failed"
        error_message = str(exc)[:500]
    except (URLError, TimeoutError, OSError) as exc:
        delivery_status = "failed"
        error_message = str(exc)[:500]

    delivery = WebhookDelivery(
        merchant_id=payment_event.merchant_id,
        webhook_endpoint_id=endpoint.id,
        payment_event_id=payment_event.id,
        status=delivery_status,
        response_status=response_status,
        error_message=error_message,
    )
    session.add(delivery)
    return delivery


def deliver_payment_event_record(
    session: Session,
    payment_event: PaymentEvent,
    *,
    timeout_seconds: float = 5.0,
) -> list[WebhookDelivery]:
    """Deliver a loaded event to all active merchant endpoints."""

    statement = select(WebhookEndpoint).where(
        WebhookEndpoint.merchant_id == payment_event.merchant_id,
        WebhookEndpoint.status == "active",
    )
    endpoints = list(session.scalars(statement).all())
    deliveries = [
        _deliver_to_endpoint(
            session=session,
            payment_event=payment_event,
            endpoint=endpoint,
            timeout_seconds=timeout_seconds,
        )
        for endpoint in endpoints
    ]

    if deliveries:
        session.commit()
        for delivery in deliveries:
            session.refresh(delivery)

    return deliveries


def deliver_payment_event(
    session: Session,
    merchant_id: uuid.UUID,
    payment_event_id: uuid.UUID,
    *,
    timeout_seconds: float = 5.0,
) -> list[WebhookDelivery]:
    """Deliver one persisted event to all active merchant endpoints."""

    payment_event = get_payment_event(
        session=session,
        merchant_id=merchant_id,
        payment_event_id=payment_event_id,
    )
    return deliver_payment_event_record(
        session=session,
        payment_event=payment_event,
        timeout_seconds=timeout_seconds,
    )


def dispatch_payment_event_safely(
    session: Session,
    payment_event: PaymentEvent,
) -> list[WebhookDelivery]:
    """Dispatch after commit without failing the lifecycle operation."""

    try:
        return deliver_payment_event_record(
            session=session,
            payment_event=payment_event,
        )
    except Exception:
        session.rollback()
        return []


def get_webhook_delivery(
    session: Session,
    merchant_id: uuid.UUID,
    webhook_delivery_id: uuid.UUID,
) -> WebhookDelivery:
    """Return a delivery attempt owned by the merchant."""

    delivery = session.get(WebhookDelivery, webhook_delivery_id)

    if delivery is None or delivery.merchant_id != merchant_id:
        raise WebhookDeliveryNotFoundError(webhook_delivery_id)

    return delivery


def retry_webhook_delivery(
    session: Session,
    merchant_id: uuid.UUID,
    webhook_delivery_id: uuid.UUID,
    *,
    timeout_seconds: float = 5.0,
) -> WebhookDelivery:
    """Retry one failed delivery as a new persisted attempt."""

    previous_delivery = get_webhook_delivery(
        session=session,
        merchant_id=merchant_id,
        webhook_delivery_id=webhook_delivery_id,
    )

    if previous_delivery.status != "failed":
        raise WebhookDeliveryNotRetryableError(webhook_delivery_id)

    endpoint = get_webhook_endpoint(
        session=session,
        merchant_id=merchant_id,
        webhook_endpoint_id=previous_delivery.webhook_endpoint_id,
    )

    if endpoint.status != "active":
        raise WebhookDeliveryNotRetryableError(webhook_delivery_id)

    payment_event = get_payment_event(
        session=session,
        merchant_id=merchant_id,
        payment_event_id=previous_delivery.payment_event_id,
    )
    delivery = _deliver_to_endpoint(
        session=session,
        payment_event=payment_event,
        endpoint=endpoint,
        timeout_seconds=timeout_seconds,
    )
    session.commit()
    session.refresh(delivery)
    return delivery


def list_webhook_deliveries(
    session: Session,
    merchant_id: uuid.UUID,
    payment_event_id: uuid.UUID | None = None,
) -> list[WebhookDelivery]:
    """List merchant webhook attempts, newest first."""

    statement = select(WebhookDelivery).where(
        WebhookDelivery.merchant_id == merchant_id,
    )

    if payment_event_id is not None:
        statement = statement.where(
            WebhookDelivery.payment_event_id == payment_event_id,
        )

    statement = statement.order_by(
        WebhookDelivery.attempted_at.desc(),
        WebhookDelivery.id.desc(),
    )
    return list(session.scalars(statement).all())
