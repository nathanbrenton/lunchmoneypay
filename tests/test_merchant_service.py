"""Tests for merchant business logic."""

from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate
from app.services.merchant import create_merchant


def test_create_merchant_adds_and_refreshes_model() -> None:
    session = MagicMock(spec=Session)
    merchant_create = MerchantCreate(name="Homesteady")

    merchant = create_merchant(
        session=session,
        merchant_create=merchant_create,
    )

    assert isinstance(merchant, Merchant)
    assert merchant.name == "Homesteady"

    session.add.assert_called_once_with(merchant)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(merchant)
