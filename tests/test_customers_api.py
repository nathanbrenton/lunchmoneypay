"""Tests for customer API endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_authenticated_credential
from app.api.v1 import customers
from app.db.session import get_db_session
from app.main import app
from app.models.customer import Customer
from app.models.merchant_api_credential import MerchantApiCredential

client = TestClient(app)


def override_get_db_session():
    """Provide a mocked database session for API tests."""

    yield MagicMock(spec=Session)


def test_create_customer_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    customer_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    credential_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=credential_id,
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        email="customer@example.com",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    monkeypatch.setattr(
        customers,
        "create_customer",
        lambda session, merchant_id, customer_create: customer,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/customers",
            json={
                "external_reference": "homesteady-user-123",
                "display_name": "Example Customer",
                "email": "customer@example.com",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": str(customer_id),
        "merchant_id": str(merchant_id),
        "external_reference": "homesteady-user-123",
        "display_name": "Example Customer",
        "email": "customer@example.com",
        "status": "active",
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "updated_at": timestamp.isoformat().replace("+00:00", "Z"),
    }


def test_create_customer_returns_conflict_for_duplicate(
    monkeypatch,
) -> None:
    merchant_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_duplicate(session, merchant_id, customer_create):
        raise customers.CustomerAlreadyExistsError(customer_create.external_reference)

    monkeypatch.setattr(
        customers,
        "create_customer",
        raise_duplicate,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.post(
            "/api/v1/customers",
            json={
                "external_reference": "homesteady-user-123",
                "display_name": "Example Customer",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "A customer with this external reference already exists for this merchant."
        ),
    }


def test_get_customer_returns_customer_owned_by_authenticated_merchant(
    monkeypatch,
) -> None:
    customer_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        email="customer@example.com",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    monkeypatch.setattr(
        customers,
        "get_customer",
        lambda session, merchant_id, customer_id: customer,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            f"/api/v1/customers/{customer_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": str(customer_id),
        "merchant_id": str(merchant_id),
        "external_reference": "homesteady-user-123",
        "display_name": "Example Customer",
        "email": "customer@example.com",
        "status": "active",
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "updated_at": timestamp.isoformat().replace("+00:00", "Z"),
    }


def test_get_customer_returns_not_found(
    monkeypatch,
) -> None:
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_not_found(session, merchant_id, customer_id):
        raise customers.CustomerNotFoundError(customer_id)

    monkeypatch.setattr(
        customers,
        "get_customer",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get(
            f"/api/v1/customers/{customer_id}",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Customer not found.",
    }


def test_list_customers_uses_authenticated_merchant_and_returns_empty_list(
    monkeypatch,
) -> None:
    """List customers within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    received_merchant_ids: list[uuid.UUID] = []

    def fake_list_customers(session, merchant_id):
        received_merchant_ids.append(merchant_id)
        return []

    monkeypatch.setattr(
        customers,
        "list_customers",
        fake_list_customers,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get("/api/v1/customers")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []
    assert received_merchant_ids == [merchant_id]


def test_list_customers_returns_serialized_customers(
    monkeypatch,
) -> None:
    """Return merchant customers as CustomerRead records."""

    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    customer = Customer(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Example Customer",
        email="customer@example.com",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    monkeypatch.setattr(
        customers,
        "list_customers",
        lambda session, merchant_id: [customer],
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.get("/api/v1/customers")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(customer.id),
            "merchant_id": str(merchant_id),
            "external_reference": "homesteady-user-123",
            "display_name": "Example Customer",
            "email": "customer@example.com",
            "status": "active",
            "created_at": timestamp.isoformat().replace("+00:00", "Z"),
            "updated_at": timestamp.isoformat().replace("+00:00", "Z"),
        },
    ]


def test_update_customer_uses_authenticated_merchant(
    monkeypatch,
) -> None:
    """Update a customer within the authenticated merchant boundary."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        external_reference="homesteady-user-123",
        display_name="Updated Customer",
        email="customer@example.com",
        status="active",
        created_at=timestamp,
        updated_at=timestamp,
    )

    received_arguments = {}

    def fake_update_customer(
        session,
        merchant_id,
        customer_id,
        customer_update,
    ):
        received_arguments["merchant_id"] = merchant_id
        received_arguments["customer_id"] = customer_id
        received_arguments["customer_update"] = customer_update
        return customer

    monkeypatch.setattr(
        customers,
        "update_customer",
        fake_update_customer,
        raising=False,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.patch(
            f"/api/v1/customers/{customer_id}",
            json={
                "display_name": "Updated Customer",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(customer_id)
    assert response.json()["display_name"] == "Updated Customer"

    assert received_arguments["merchant_id"] == merchant_id
    assert received_arguments["customer_id"] == customer_id
    assert received_arguments["customer_update"].model_dump(
        exclude_unset=True,
    ) == {
        "display_name": "Updated Customer",
    }


def test_update_customer_returns_not_found(
    monkeypatch,
) -> None:
    """Return 404 when the customer is missing or belongs to another merchant."""

    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    def raise_not_found(
        session,
        merchant_id,
        customer_id,
        customer_update,
    ):
        raise customers.CustomerNotFoundError(customer_id)

    monkeypatch.setattr(
        customers,
        "update_customer",
        raise_not_found,
    )

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_authenticated_credential] = lambda: credential

    try:
        response = client.patch(
            f"/api/v1/customers/{customer_id}",
            json={
                "status": "disabled",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Customer not found.",
    }
