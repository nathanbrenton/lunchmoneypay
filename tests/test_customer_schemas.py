"""Tests for customer API schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate, CustomerRead


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
