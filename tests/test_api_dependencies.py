"""Tests for shared API authentication dependencies."""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api import dependencies
from app.models.merchant_api_credential import MerchantApiCredential


def test_get_authenticated_credential_returns_matching_record(
    monkeypatch,
) -> None:
    session = MagicMock(spec=Session)
    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        key_prefix="lmp_test_a1b2c3d4e5f6",
        secret_hash="stored-hash",
        status="active",
    )

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        lambda session, api_key, pepper: credential,
    )

    result = dependencies.get_authenticated_credential(
        session=session,
        api_key="lmp_test_a1b2c3d4e5f6.example-secret",
    )

    assert result is credential


def test_get_authenticated_credential_rejects_missing_key() -> None:
    session = MagicMock(spec=Session)

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_authenticated_credential(
            session=session,
            api_key=None,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "API key is required."


def test_get_authenticated_credential_rejects_invalid_key(
    monkeypatch,
) -> None:
    session = MagicMock(spec=Session)

    def raise_invalid(session, api_key, pepper):
        raise dependencies.InvalidApiKeyError("Invalid API key.")

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        raise_invalid,
    )

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_authenticated_credential(
            session=session,
            api_key="lmp_test_invalid.example-secret",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid API key."


def test_get_authenticated_credential_rejects_inactive_key(
    monkeypatch,
) -> None:
    session = MagicMock(spec=Session)

    def raise_inactive(session, api_key, pepper):
        raise dependencies.InactiveApiCredentialError("API credential is not active.")

    monkeypatch.setattr(
        dependencies,
        "authenticate_api_key",
        raise_inactive,
    )

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_authenticated_credential(
            session=session,
            api_key="lmp_test_revoked.example-secret",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "API credential is not active."
