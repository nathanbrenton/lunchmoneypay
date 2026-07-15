"""Tests for merchant API credential business logic."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.models.merchant_api_credential import MerchantApiCredential
from app.services.exceptions import MerchantNotFoundError
from app.services.merchant_api_credential import (
    create_merchant_api_credential,
)

TEST_PEPPER = "development-only-test-pepper"


def test_create_merchant_api_credential_persists_safe_values() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    session.get.return_value = Merchant(
        id=merchant_id,
        name="Homesteady",
        status="active",
    )

    result = create_merchant_api_credential(
        session=session,
        merchant_id=merchant_id,
        pepper=TEST_PEPPER,
    )

    credential = result.credential

    assert isinstance(credential, MerchantApiCredential)
    assert credential.merchant_id == merchant_id
    assert credential.key_prefix.startswith("lmp_test_")
    assert credential.secret_hash != result.api_key
    assert result.api_key.startswith(f"{credential.key_prefix}.")

    session.add.assert_called_once_with(credential)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(credential)


def test_create_merchant_api_credential_returns_unique_keys() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    session.get.return_value = Merchant(
        id=merchant_id,
        name="Homesteady",
        status="active",
    )

    first = create_merchant_api_credential(
        session=session,
        merchant_id=merchant_id,
        pepper=TEST_PEPPER,
    )
    second = create_merchant_api_credential(
        session=session,
        merchant_id=merchant_id,
        pepper=TEST_PEPPER,
    )

    assert first.api_key != second.api_key
    assert first.credential.key_prefix != second.credential.key_prefix
    assert first.credential.secret_hash != second.credential.secret_hash


def test_create_merchant_api_credential_rejects_missing_merchant() -> None:
    session = MagicMock(spec=Session)
    session.get.return_value = None
    merchant_id = uuid.uuid4()

    with pytest.raises(MerchantNotFoundError):
        create_merchant_api_credential(
            session=session,
            merchant_id=merchant_id,
            pepper=TEST_PEPPER,
        )

    session.get.assert_called_once_with(Merchant, merchant_id)
    session.add.assert_not_called()
    session.commit.assert_not_called()
    session.refresh.assert_not_called()
