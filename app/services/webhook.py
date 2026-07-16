"""Webhook registration, signing, and delivery operations."""

import hashlib
import hmac
import json
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment_event import PaymentEvent
from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_endpoint import WebhookEndpoint
from app.schemas.webhook import WebhookEndpointCreate
from app.services.exceptions import (
    WebhookEndpointAlreadyExistsError,
    WebhookEndpointNotFoundError,
)
from app.services.payment_event import get_payment_event


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
    statement = select(WebhookEndpoint).where(
        WebhookEndpoint.merchant_id == merchant_id,
        WebhookEndpoint.status == "active",
    )
    endpoints = list(session.scalars(statement).all())
    payload_body = serialize_payment_event(payment_event)
    timestamp = int(time.time())
    deliveries: list[WebhookDelivery] = []

    for endpoint in endpoints:
        signature = create_webhook_signature(
            endpoint.signing_secret,
            timestamp,
            payload_body,
        )
        request = Request(
            endpoint.url,
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
            with urlopen(request, timeout=timeout_seconds) as response:
                response_status = response.status
                delivery_status = (
                    "succeeded" if 200 <= response.status < 300 else "failed"
                )
        except HTTPError as exc:
            response_status = exc.code
            delivery_status = "failed"
            error_message = str(exc)[:500]
        except (URLError, TimeoutError, OSError) as exc:
            delivery_status = "failed"
            error_message = str(exc)[:500]

        delivery = WebhookDelivery(
            merchant_id=merchant_id,
            webhook_endpoint_id=endpoint.id,
            payment_event_id=payment_event.id,
            status=delivery_status,
            response_status=response_status,
            error_message=error_message,
        )
        session.add(delivery)
        deliveries.append(delivery)

    if deliveries:
        session.commit()
        for delivery in deliveries:
            session.refresh(delivery)

    return deliveries


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
