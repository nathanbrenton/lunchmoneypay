"""Tests for customer API schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate


def test_customer_create_accepts_valid_fields() -> None:
    customer = CustomerCreate(
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        email="customer@example.com",
    )

    assert customer.external_reference == "homesteady-user-123"
    assert customer.display_name == "Example Customer"
    assert customer.email == "customer@example.com"


def test_customer_create_allows_missing_email() -> None:
    customer = CustomerCreate(
        external_reference="homesteady-user-123",
        display_name="Example Customer",
    )

    assert customer.email is None


def test_customer_create_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        CustomerCreate(
            external_reference="homesteady-user-123",
            display_name="Example Customer",
            email="not-an-email-address",
        )


def test_customer_create_rejects_empty_external_reference() -> None:
    with pytest.raises(ValidationError):
        CustomerCreate(
            external_reference="",
            display_name="Example Customer",
        )


def test_customer_read_accepts_expected_fields() -> None:
    customer_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    customer = CustomerRead(
        id=customer_id,
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        email="customer@example.com",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert customer.id == customer_id
    assert customer.merchant_id == merchant_id
    assert customer.status == "active"


def test_customer_update_accepts_partial_fields() -> None:
    """Allow callers to update only the fields they provide."""

    customer = CustomerUpdate(
        display_name="Updated Customer",
    )

    assert customer.display_name == "Updated Customer"
    assert customer.email is None
    assert customer.status is None


def test_customer_update_accepts_email_and_status() -> None:
    """Accept valid optional update fields."""

    customer = CustomerUpdate(
        email="updated@example.com",
        status="disabled",
    )

    assert str(customer.email) == "updated@example.com"
    assert customer.status == "disabled"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("display_name", ""),
        ("email", "not-an-email"),
        ("status", "deleted"),
    ],
)
def test_customer_update_rejects_invalid_fields(
    field_name: str,
    field_value: str,
) -> None:
    """Reject invalid customer update values."""

    with pytest.raises(ValidationError):
        CustomerUpdate(
            **{field_name: field_value},
        )


def test_customer_update_tracks_only_provided_fields() -> None:
    """Preserve which fields were explicitly included in the PATCH body."""

    customer = CustomerUpdate(
        status="disabled",
    )

    assert customer.model_dump(exclude_unset=True) == {
        "status": "disabled",
    }


@pytest.mark.parametrize(
    "field_name",
    [
        "display_name",
        "status",
    ],
)
def test_customer_update_rejects_null_for_required_model_fields(
    field_name: str,
) -> None:
    """Reject null for customer fields that cannot be cleared."""

    with pytest.raises(ValidationError):
        CustomerUpdate(
            **{field_name: None},
        )
