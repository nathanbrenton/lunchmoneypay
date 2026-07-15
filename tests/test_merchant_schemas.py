"""Tests for merchant API schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.merchant import MerchantCreate, MerchantRead


def test_merchant_create_accepts_valid_name() -> None:
    merchant = MerchantCreate(name="Homesteady")

    assert merchant.name == "Homesteady"


def test_merchant_create_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        MerchantCreate(name="")


def test_merchant_read_accepts_expected_fields() -> None:
    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    merchant = MerchantRead(
        id=merchant_id,
        name="Homesteady",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    assert merchant.id == merchant_id
    assert merchant.status == "active"
