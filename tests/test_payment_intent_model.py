"""Tests for the payment-intent database model."""

import uuid

from app.models.payment_intent import PaymentIntent


def test_payment_intent_uses_expected_table_name() -> None:
    """Map payment intents to the expected database table."""

    assert PaymentIntent.__tablename__ == "payment_intents"


def test_payment_intent_requires_merchant_id() -> None:
    """Require each payment intent to belong to one merchant."""

    column = PaymentIntent.__table__.columns["merchant_id"]

    assert column.nullable is False


def test_payment_intent_requires_customer_id() -> None:
    """Require each payment intent to reference one customer."""

    column = PaymentIntent.__table__.columns["customer_id"]

    assert column.nullable is False


def test_payment_intent_requires_amount_minor() -> None:
    """Store the payment amount in the currency's smallest unit."""

    column = PaymentIntent.__table__.columns["amount_minor"]

    assert column.nullable is False


def test_payment_intent_requires_currency() -> None:
    """Require an ISO-style three-letter currency code."""

    column = PaymentIntent.__table__.columns["currency"]

    assert column.nullable is False
    assert column.type.length == 3


def test_payment_intent_defaults_to_requires_payment_method() -> None:
    """Configure the initial payment-intent lifecycle state."""

    column = PaymentIntent.__table__.columns["status"]

    assert column.nullable is False
    assert column.default is not None
    assert column.default.arg == "requires_payment_method"


def test_payment_intent_has_created_and_updated_timestamps() -> None:
    """Track when payment intents are created and modified."""

    created_at = PaymentIntent.__table__.columns["created_at"]
    updated_at = PaymentIntent.__table__.columns["updated_at"]

    assert created_at.nullable is False
    assert updated_at.nullable is False


def test_payment_intent_has_status_check_constraint() -> None:
    """Restrict payment intents to supported lifecycle states."""

    constraint_sql = {
        str(constraint.sqltext)
        for constraint in PaymentIntent.__table__.constraints
        if hasattr(constraint, "sqltext")
    }

    assert (
        "status IN "
        "('requires_payment_method', 'processing', 'succeeded', 'failed', 'canceled')"
        in constraint_sql
    )


def test_payment_intent_requires_positive_amount() -> None:
    """Require payment amounts greater than zero."""

    constraint_sql = {
        str(constraint.sqltext)
        for constraint in PaymentIntent.__table__.constraints
        if hasattr(constraint, "sqltext")
    }

    assert "amount_minor > 0" in constraint_sql


def test_payment_intent_requires_uppercase_currency_code() -> None:
    """Require a three-letter uppercase currency code."""

    constraint_sql = {
        str(constraint.sqltext)
        for constraint in PaymentIntent.__table__.constraints
        if hasattr(constraint, "sqltext")
    }

    assert "currency ~ '^[A-Z]{3}$'" in constraint_sql


def test_payment_intent_requires_external_reference() -> None:
    """Require a merchant-side reference for payment correlation."""

    column = PaymentIntent.__table__.columns["external_reference"]

    assert column.nullable is False
    assert column.type.length == 255


def test_payment_intent_external_reference_is_unique_per_merchant() -> None:
    """Prevent duplicate merchant-side payment references."""

    unique_constraints = {
        tuple(column.name for column in constraint.columns)
        for constraint in PaymentIntent.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("merchant_id", "external_reference") in unique_constraints


def test_payment_intent_table_is_registered_with_base_metadata() -> None:
    """Expose the payment-intent table to Alembic metadata."""

    from app.db.base import Base

    assert "payment_intents" in Base.metadata.tables


def test_payment_intent_has_database_defaults() -> None:
    """Provide database defaults for status and timestamps."""

    status = PaymentIntent.__table__.columns["status"]
    created_at = PaymentIntent.__table__.columns["created_at"]
    updated_at = PaymentIntent.__table__.columns["updated_at"]

    assert status.server_default is not None
    assert created_at.server_default is not None
    assert updated_at.server_default is not None


def test_payment_intent_allows_optional_last_error_code() -> None:
    """Store the latest mock processing error without ending the intent."""

    column = PaymentIntent.__table__.columns["last_error_code"]

    assert column.nullable is True
    assert column.type.length == 50


def test_payment_intent_has_optional_payment_method_foreign_key() -> None:
    """Allow a payment method to be attached after intent creation."""

    payment_method_id = uuid.uuid4()

    payment_intent = PaymentIntent(
        merchant_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        payment_method_id=payment_method_id,
        external_reference="homesteady-payment-with-method",
        amount_minor=2500,
        currency="USD",
    )

    assert payment_intent.payment_method_id == payment_method_id

    column = PaymentIntent.__table__.c.payment_method_id

    assert column.nullable is True
    assert len(column.foreign_keys) == 1
    assert next(iter(column.foreign_keys)).target_fullname == "payment_methods.id"
