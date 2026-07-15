"""Tests for customer business logic."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.customer import (
    create_customer,
    get_customer,
    list_customers,
    update_customer,
)
from app.services.exceptions import (
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
)


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


def test_get_customer_returns_customer_owned_by_merchant() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        status="active",
    )

    session.get.return_value = customer

    result = get_customer(
        session=session,
        merchant_id=merchant_id,
        customer_id=customer_id,
    )

    assert result is customer
    session.get.assert_called_once_with(Customer, customer_id)


def test_get_customer_rejects_missing_customer() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    session.get.return_value = None

    with pytest.raises(CustomerNotFoundError):
        get_customer(
            session=session,
            merchant_id=merchant_id,
            customer_id=customer_id,
        )


def test_get_customer_rejects_customer_owned_by_another_merchant() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    customer = Customer(
        id=customer_id,
        merchant_id=uuid.uuid4(),
        external_reference="other-merchant-user-123",
        display_name="Other Customer",
        status="active",
    )

    session.get.return_value = customer

    with pytest.raises(CustomerNotFoundError):
        get_customer(
            session=session,
            merchant_id=merchant_id,
            customer_id=customer_id,
        )


def test_list_customers_returns_merchant_owned_customers() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()

    first = Customer(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="First Customer",
        status="active",
    )
    second = Customer(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        external_reference="homesteady-user-456",
        display_name="Second Customer",
        status="active",
    )

    session.scalars.return_value = [first, second]

    result = list_customers(
        session=session,
        merchant_id=merchant_id,
    )

    assert result == [first, second]
    session.scalars.assert_called_once()


def test_list_customers_returns_empty_list() -> None:
    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    session.scalars.return_value = []

    result = list_customers(
        session=session,
        merchant_id=merchant_id,
    )

    assert result == []
    session.scalars.assert_called_once()


def test_update_customer_changes_only_provided_fields() -> None:
    """Update supplied fields while preserving omitted customer data."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Original Customer",
        email="original@example.com",
        status="active",
    )

    session.get.return_value = customer

    customer_update = CustomerUpdate(
        display_name="Updated Customer",
    )

    result = update_customer(
        session=session,
        merchant_id=merchant_id,
        customer_id=customer_id,
        customer_update=customer_update,
    )

    assert result is customer
    assert customer.display_name == "Updated Customer"
    assert customer.email == "original@example.com"
    assert customer.status == "active"

    session.get.assert_called_once_with(Customer, customer_id)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(customer)


def test_update_customer_rejects_customer_owned_by_another_merchant() -> None:
    """Hide customers that do not belong to the requesting merchant."""

    session = MagicMock(spec=Session)
    authenticated_merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    customer = Customer(
        id=customer_id,
        merchant_id=uuid.uuid4(),
        external_reference="other-merchant-user",
        display_name="Other Merchant Customer",
        email="other@example.com",
        status="active",
    )

    session.get.return_value = customer

    with pytest.raises(CustomerNotFoundError):
        update_customer(
            session=session,
            merchant_id=authenticated_merchant_id,
            customer_id=customer_id,
            customer_update=CustomerUpdate(
                status="disabled",
            ),
        )

    session.commit.assert_not_called()
    session.refresh.assert_not_called()
