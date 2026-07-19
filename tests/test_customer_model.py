"""Tests for the customer database model."""

from app.models.customer import Customer


def test_customer_uses_expected_table_name() -> None:
    assert Customer.__tablename__ == "customers"


def test_customer_accepts_expected_attributes() -> None:
    customer = Customer(
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        email="customer@example.com",
        status="active",
    )

    assert customer.external_reference == "homesteady-user-123"
    assert customer.display_name == "Example Customer"
    assert customer.email == "customer@example.com"
    assert customer.status == "active"


def test_customer_contains_expected_columns() -> None:
    assert set(Customer.__table__.columns.keys()) == {
        "id",
        "merchant_id",
        "external_reference",
        "display_name",
        "email",
        "status",
        "created_at",
        "updated_at",
    }


def test_customer_defines_expected_defaults() -> None:
    columns = Customer.__table__.columns

    assert columns["id"].default is not None
    assert columns["status"].default is not None
    assert columns["created_at"].server_default is not None
    assert columns["updated_at"].server_default is not None


def test_customer_external_reference_is_unique_per_merchant() -> None:
    constraint_names = {
        constraint.name for constraint in Customer.__table__.constraints
    }

    assert "uq_customers_merchant_external_reference" in constraint_names
