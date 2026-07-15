"""Tests for merchant business logic."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate
from app.services.exceptions import MerchantAlreadyExistsError
from app.services.merchant import create_merchant


def test_create_merchant_commits_and_refreshes_model() -> None:
    session = MagicMock(spec=Session)
    merchant_create = MerchantCreate(name="Homesteady")

    merchant = create_merchant(
        session=session,
        merchant_create=merchant_create,
    )

    assert isinstance(merchant, Merchant)
    assert merchant.name == "Homesteady"

    session.add.assert_called_once_with(merchant)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(merchant)
    session.rollback.assert_not_called()


def test_create_merchant_rolls_back_duplicate_name() -> None:
    session = MagicMock(spec=Session)
    session.commit.side_effect = IntegrityError(
        statement=None,
        params=None,
        orig=Exception("duplicate merchant"),
    )

    merchant_create = MerchantCreate(name="Homesteady")

    with pytest.raises(MerchantAlreadyExistsError):
        create_merchant(
            session=session,
            merchant_create=merchant_create,
        )

    session.rollback.assert_called_once_with()
    session.refresh.assert_not_called()
