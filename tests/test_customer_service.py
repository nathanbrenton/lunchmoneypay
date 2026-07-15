"""Tests for customer business logic."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate
from app.services.customer import create_customer
from app.services.exceptions import CustomerAlreadyExistsError


def test_create_customer_commits_and_refreshes_model() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_create = CustomerCreate(
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        email="customer@example.com",
    )

    customer = create_customer(
        session=session,
        merchant_id=merchant_id,
        customer_create=customer_create,
    )

    assert isinstance(customer, Customer)
    assert customer.merchant_id == merchant_id
    assert customer.external_reference == "homesteady-user-123"
    assert customer.display_name == "Example Customer"
    assert customer.email == "customer@example.com"

    session.add.assert_called_once_with(customer)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(customer)
    session.rollback.assert_not_called()


def test_create_customer_rolls_back_duplicate_external_reference() -> None:
    session = MagicMock(spec=Session)
    session.commit.side_effect = IntegrityError(
        statement=None,
        params=None,
        orig=Exception("duplicate customer"),
    )

    merchant_id = uuid.uuid4()
    customer_create = CustomerCreate(
        external_reference="homesteady-user-123",
        display_name="Example Customer",
    )

    with pytest.raises(CustomerAlreadyExistsError):
        create_customer(
            session=session,
            merchant_id=merchant_id,
            customer_create=customer_create,
        )

    session.rollback.assert_called_once_with()
    session.refresh.assert_not_called()
