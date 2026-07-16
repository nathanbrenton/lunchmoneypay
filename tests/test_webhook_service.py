"""Tests for webhook signing and delivery operations."""

import hashlib
import hmac
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

import app.services.webhook as webhook_service
from app.models.payment_event import PaymentEvent
from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_endpoint import WebhookEndpoint


class SuccessfulResponse:
    """Minimal context-managed outbound HTTP response."""

    status = 204

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_create_webhook_signature_uses_timestamp_and_payload() -> None:
    """Sign the exact timestamped request body."""

    payload = b'{"example":true}'
    timestamp = 1234567890
    secret = "a" * 32

    result = webhook_service.create_webhook_signature(
        secret,
        timestamp,
        payload,
    )

    expected = hmac.new(
        secret.encode(),
        str(timestamp).encode() + b"." + payload,
        hashlib.sha256,
    ).hexdigest()

    assert result == f"t={timestamp},v1={expected}"


def test_deliver_payment_event_records_success(monkeypatch) -> None:
    """Post a signed event and persist a successful attempt."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    event_id = uuid.uuid4()
    endpoint_id = uuid.uuid4()

    payment_event = PaymentEvent(
        id=event_id,
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload={"status": "succeeded"},
        created_at=datetime.now(UTC),
    )
    endpoint = WebhookEndpoint(
        id=endpoint_id,
        merchant_id=merchant_id,
        url="https://example.test/webhooks",
        signing_secret="a" * 32,
        status="active",
    )

    monkeypatch.setattr(
        webhook_service,
        "get_payment_event",
        lambda **kwargs: payment_event,
    )
    monkeypatch.setattr(
        webhook_service,
        "urlopen",
        lambda request, timeout: SuccessfulResponse(),
    )
    session.scalars.return_value.all.return_value = [endpoint]

    result = webhook_service.deliver_payment_event(
        session=session,
        merchant_id=merchant_id,
        payment_event_id=event_id,
    )

    assert len(result) == 1
    assert result[0].status == "succeeded"
    assert result[0].response_status == 204
    assert result[0].webhook_endpoint_id == endpoint_id
    assert result[0].payment_event_id == event_id
    session.commit.assert_called_once_with()


def test_deliver_payment_event_records_network_failure(monkeypatch) -> None:
    """Persist a failed attempt without raising the network error."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    event_id = uuid.uuid4()
    payment_event = PaymentEvent(
        id=event_id,
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.payment_failed",
        payload={"status": "requires_payment_method"},
        created_at=datetime.now(UTC),
    )
    endpoint = WebhookEndpoint(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        url="https://example.test/webhooks",
        signing_secret="a" * 32,
        status="active",
    )

    monkeypatch.setattr(
        webhook_service,
        "get_payment_event",
        lambda **kwargs: payment_event,
    )

    def raise_timeout(request, timeout):
        raise TimeoutError("mock timeout")

    monkeypatch.setattr(webhook_service, "urlopen", raise_timeout)
    session.scalars.return_value.all.return_value = [endpoint]

    result = webhook_service.deliver_payment_event(
        session=session,
        merchant_id=merchant_id,
        payment_event_id=event_id,
    )

    assert len(result) == 1
    assert result[0].status == "failed"
    assert result[0].response_status is None
    assert "mock timeout" in result[0].error_message
    session.commit.assert_called_once_with()


def test_deliver_payment_event_returns_empty_without_active_endpoints(
    monkeypatch,
) -> None:
    """Return no attempts when the merchant has no active destination."""

    session = MagicMock(spec=Session)
    payment_event = PaymentEvent(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload={"status": "succeeded"},
        created_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        webhook_service,
        "get_payment_event",
        lambda **kwargs: payment_event,
    )
    session.scalars.return_value.all.return_value = []

    result = webhook_service.deliver_payment_event(
        session=session,
        merchant_id=payment_event.merchant_id,
        payment_event_id=payment_event.id,
    )

    assert result == []
    session.commit.assert_not_called()


def test_dispatch_payment_event_safely_isolates_delivery_failure(
    monkeypatch,
) -> None:
    """Do not fail a committed lifecycle operation when dispatch crashes."""

    session = MagicMock(spec=Session)
    payment_event = PaymentEvent(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload={"status": "succeeded"},
        created_at=datetime.now(UTC),
    )

    def raise_delivery_error(**kwargs):
        raise RuntimeError("delivery persistence failed")

    monkeypatch.setattr(
        webhook_service,
        "deliver_payment_event_record",
        raise_delivery_error,
    )

    result = webhook_service.dispatch_payment_event_safely(
        session=session,
        payment_event=payment_event,
    )

    assert result == []
    session.rollback.assert_called_once_with()


def test_retry_webhook_delivery_creates_new_attempt(
    monkeypatch,
) -> None:
    """Retry a failed attempt against its original endpoint and event."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    endpoint = WebhookEndpoint(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        url="https://example.test/webhooks",
        signing_secret="a" * 32,
        status="active",
    )
    payment_event = PaymentEvent(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        event_type="payment_intent.succeeded",
        payload={"status": "succeeded"},
        created_at=datetime.now(UTC),
    )
    previous_delivery = WebhookDelivery(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        webhook_endpoint_id=endpoint.id,
        payment_event_id=payment_event.id,
        status="failed",
    )
    retried_delivery = WebhookDelivery(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        webhook_endpoint_id=endpoint.id,
        payment_event_id=payment_event.id,
        status="succeeded",
        response_status=204,
    )

    monkeypatch.setattr(
        webhook_service,
        "get_webhook_delivery",
        lambda **kwargs: previous_delivery,
    )
    monkeypatch.setattr(
        webhook_service,
        "get_webhook_endpoint",
        lambda **kwargs: endpoint,
    )
    monkeypatch.setattr(
        webhook_service,
        "get_payment_event",
        lambda **kwargs: payment_event,
    )
    monkeypatch.setattr(
        webhook_service,
        "_deliver_to_endpoint",
        lambda **kwargs: retried_delivery,
    )

    result = webhook_service.retry_webhook_delivery(
        session=session,
        merchant_id=merchant_id,
        webhook_delivery_id=previous_delivery.id,
    )

    assert result is retried_delivery
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(retried_delivery)
