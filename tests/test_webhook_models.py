"""Tests for webhook persistence models."""

from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_endpoint import WebhookEndpoint


def test_webhook_models_use_expected_tables() -> None:
    """Store registrations and delivery attempts separately."""

    assert WebhookEndpoint.__tablename__ == "webhook_endpoints"
    assert WebhookDelivery.__tablename__ == "webhook_deliveries"


def test_webhook_models_have_status_constraints() -> None:
    """Restrict endpoint and delivery statuses."""

    endpoint_constraints = {
        constraint.name
        for constraint in WebhookEndpoint.__table__.constraints
        if constraint.name is not None
    }
    delivery_constraints = {
        constraint.name
        for constraint in WebhookDelivery.__table__.constraints
        if constraint.name is not None
    }

    assert "ck_webhook_endpoints_status" in endpoint_constraints
    assert "uq_webhook_endpoints_merchant_url" in endpoint_constraints
    assert "ck_webhook_deliveries_status" in delivery_constraints
