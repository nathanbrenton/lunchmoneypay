"""Webhook endpoint and delivery API operations."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_endpoint import WebhookEndpoint
from app.schemas.webhook import (
    WebhookDeliveryRead,
    WebhookEndpointCreate,
    WebhookEndpointRead,
)
from app.services.exceptions import (
    PaymentEventNotFoundError,
    WebhookEndpointAlreadyExistsError,
    WebhookEndpointNotFoundError,
)
from app.services.webhook import (
    create_webhook_endpoint,
    deactivate_webhook_endpoint,
    deliver_payment_event,
    get_webhook_endpoint,
    list_webhook_deliveries,
    list_webhook_endpoints,
)

router = APIRouter(prefix="/webhook-endpoints", tags=["webhooks"])


@router.post(
    "",
    response_model=WebhookEndpointRead,
    status_code=status.HTTP_201_CREATED,
)
def create_webhook_endpoint_endpoint(
    endpoint_create: WebhookEndpointCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> WebhookEndpoint:
    """Register a webhook destination for the authenticated merchant."""

    try:
        return create_webhook_endpoint(
            session=session,
            merchant_id=credential.merchant_id,
            endpoint_create=endpoint_create,
        )
    except WebhookEndpointAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This webhook URL is already registered.",
        ) from exc


@router.get("", response_model=list[WebhookEndpointRead])
def list_webhook_endpoints_endpoint(
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> list[WebhookEndpoint]:
    """List webhook destinations owned by the merchant."""

    return list_webhook_endpoints(
        session=session,
        merchant_id=credential.merchant_id,
    )


@router.get("/{webhook_endpoint_id}", response_model=WebhookEndpointRead)
def get_webhook_endpoint_endpoint(
    webhook_endpoint_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> WebhookEndpoint:
    """Retrieve a merchant-owned webhook destination."""

    try:
        return get_webhook_endpoint(
            session=session,
            merchant_id=credential.merchant_id,
            webhook_endpoint_id=webhook_endpoint_id,
        )
    except WebhookEndpointNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found.",
        ) from exc


@router.post(
    "/{webhook_endpoint_id}/deactivate",
    response_model=WebhookEndpointRead,
)
def deactivate_webhook_endpoint_endpoint(
    webhook_endpoint_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> WebhookEndpoint:
    """Deactivate a merchant-owned webhook destination."""

    try:
        return deactivate_webhook_endpoint(
            session=session,
            merchant_id=credential.merchant_id,
            webhook_endpoint_id=webhook_endpoint_id,
        )
    except WebhookEndpointNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook endpoint not found.",
        ) from exc


delivery_router = APIRouter(prefix="/webhook-deliveries", tags=["webhooks"])


@delivery_router.post(
    "/payment-events/{payment_event_id}",
    response_model=list[WebhookDeliveryRead],
)
def deliver_payment_event_endpoint(
    payment_event_id: uuid.UUID,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> list[WebhookDelivery]:
    """Deliver a persisted payment event to all active destinations."""

    try:
        return deliver_payment_event(
            session=session,
            merchant_id=credential.merchant_id,
            payment_event_id=payment_event_id,
        )
    except PaymentEventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment event not found.",
        ) from exc


@delivery_router.get("", response_model=list[WebhookDeliveryRead])
def list_webhook_deliveries_endpoint(
    credential: AuthenticatedCredential,
    session: DatabaseSession,
    payment_event_id: uuid.UUID | None = None,
) -> list[WebhookDelivery]:
    """List merchant webhook-delivery attempts."""

    return list_webhook_deliveries(
        session=session,
        merchant_id=credential.merchant_id,
        payment_event_id=payment_event_id,
    )
