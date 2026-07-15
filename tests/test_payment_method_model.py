"""Tests for the mock payment-method database model."""

from app.models.payment_method import PaymentMethod


def test_payment_method_defines_expected_columns() -> None:
    """Define the reusable mock-card fields."""

    columns = PaymentMethod.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "merchant_id",
        "customer_id",
        "type",
        "card_brand",
        "card_last4",
        "card_exp_month",
        "card_exp_year",
        "status",
        "test_scenario",
        "created_at",
        "updated_at",
    }


def test_payment_method_defines_expected_defaults() -> None:
    """Configure default status, scenario, identifiers, and timestamps."""

    columns = PaymentMethod.__table__.columns

    assert columns["id"].default is not None

    assert columns["status"].default is not None
    assert columns["status"].default.arg == "active"
    assert columns["status"].server_default is not None

    assert columns["test_scenario"].default is not None
    assert columns["test_scenario"].default.arg == "success"
    assert columns["test_scenario"].server_default is not None

    assert columns["created_at"].server_default is not None
    assert columns["updated_at"].server_default is not None


def test_payment_method_defines_expected_constraints() -> None:
    """Restrict mock cards to supported values and formats."""

    constraint_sql = {
        str(constraint.sqltext)
        for constraint in PaymentMethod.__table__.constraints
        if hasattr(constraint, "sqltext")
    }

    assert "type IN ('card')" in constraint_sql
    assert "status IN ('active', 'inactive')" in constraint_sql
    assert "test_scenario IN ('success', 'card_declined')" in constraint_sql
    assert "card_exp_month BETWEEN 1 AND 12" in constraint_sql
    assert "card_last4 ~ '^[0-9]{4}$'" in constraint_sql


def test_payment_method_is_registered_with_base_metadata() -> None:
    """Register the model for migrations and table creation."""

    from app.db.base import Base

    assert "payment_methods" in Base.metadata.tables
