"""Source-level safeguards for the LunchMoneyPay demo checkout contract."""

from pathlib import Path

from app.models.payment_intent import PaymentIntent
from app.schemas.checkout_session import DemoCheckoutSessionCreate


def test_checkout_schema_contains_no_card_entry_fields() -> None:
    fields = set(DemoCheckoutSessionCreate.model_fields)

    assert fields == {
        "customer_external_reference",
        "customer_display_name",
        "customer_email",
        "external_reference",
        "amount_minor",
        "currency",
        "test_scenario",
    }


def test_failed_payment_state_is_database_bounded() -> None:
    constraints = {
        constraint.name: str(constraint.sqltext)
        for constraint in PaymentIntent.__table__.constraints
        if getattr(constraint, "sqltext", None) is not None
    }

    assert "failed" in constraints["ck_payment_intents_status"]


def test_checkout_endpoint_uses_no_raw_card_terms() -> None:
    source = Path("app/api/v1/checkout_sessions.py").read_text()
    service = Path("app/services/checkout_session.py").read_text()
    bootstrap = Path("scripts/bootstrap_demo.py").read_text()

    assert "card_number" not in source
    assert "card_number" not in service
    assert "cvv" not in source.lower()
    assert "cvv" not in service.lower()
    assert "card_number" not in bootstrap
    assert "card_exp" not in bootstrap
    assert "cvv" not in bootstrap.lower()


def test_checkout_idempotency_hash_covers_scenario(
    monkeypatch,
) -> None:
    import uuid

    import pytest

    import app.services.checkout_session as checkout_service
    from app.models.idempotency_record import IdempotencyRecord
    from app.schemas.checkout_session import DemoCheckoutSessionCreate
    from app.services.exceptions import IdempotencyKeyConflictError
    from app.services.idempotency import hash_request_payload

    success = DemoCheckoutSessionCreate(
        customer_external_reference="customer-1",
        customer_display_name="Customer One",
        customer_email="customer@example.com",
        external_reference="order-1",
        amount_minor=125000,
        currency="USD",
        test_scenario="success",
    )
    declined = success.model_copy(update={"test_scenario": "card_declined"})
    record = IdempotencyRecord(
        merchant_id=uuid.uuid4(),
        idempotency_key="checkout-key-1",
        operation=checkout_service.CHECKOUT_OPERATION,
        request_hash=hash_request_payload(success),
        resource_type=checkout_service.CHECKOUT_RESOURCE_TYPE,
        resource_id=uuid.uuid4(),
    )
    monkeypatch.setattr(
        checkout_service,
        "get_idempotency_record",
        lambda **kwargs: record,
    )

    with pytest.raises(IdempotencyKeyConflictError):
        checkout_service.create_demo_checkout_session(
            object(),
            merchant_id=record.merchant_id,
            payload=declined,
            idempotency_key=record.idempotency_key,
            expiration_year=2099,
        )
