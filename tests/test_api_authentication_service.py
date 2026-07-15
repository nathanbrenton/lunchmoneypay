"""Tests for merchant API-key authentication."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.api_keys import generate_api_key
from app.models.merchant_api_credential import MerchantApiCredential
from app.services.api_authentication import (
    authenticate_api_key,
    extract_key_prefix,
)
from app.services.exceptions import InvalidApiKeyError

TEST_PEPPER = "development-only-test-pepper"


def test_extract_key_prefix_returns_public_component() -> None:
    api_key = "lmp_test_a1b2c3d4e5f6.example-secret"

    assert extract_key_prefix(api_key) == "lmp_test_a1b2c3d4e5f6"


@pytest.mark.parametrize(
    "api_key",
    [
        "",
        "missing-period",
        ".missing-prefix",
        "lmp_test_a1b2c3d4e5f6.",
        "unexpected_prefix.secret",
    ],
)
def test_extract_key_prefix_rejects_malformed_key(
    api_key: str,
) -> None:
    with pytest.raises(InvalidApiKeyError):
        extract_key_prefix(api_key)


def test_authenticate_api_key_returns_matching_credential() -> None:
    session = MagicMock(spec=Session)
    generated = generate_api_key(TEST_PEPPER)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        key_prefix=generated.key_prefix,
        secret_hash=generated.secret_hash,
        status="active",
    )

    session.scalar.return_value = credential

    result = authenticate_api_key(
        session=session,
        api_key=generated.api_key,
        pepper=TEST_PEPPER,
    )

    assert result is credential
    session.scalar.assert_called_once()


def test_authenticate_api_key_rejects_unknown_prefix() -> None:
    session = MagicMock(spec=Session)
    session.scalar.return_value = None

    with pytest.raises(InvalidApiKeyError):
        authenticate_api_key(
            session=session,
            api_key="lmp_test_a1b2c3d4e5f6.example-secret",
            pepper=TEST_PEPPER,
        )


def test_authenticate_api_key_rejects_wrong_secret() -> None:
    session = MagicMock(spec=Session)
    generated = generate_api_key(TEST_PEPPER)

    credential = MerchantApiCredential(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        key_prefix=generated.key_prefix,
        secret_hash=generated.secret_hash,
        status="active",
    )

    session.scalar.return_value = credential

    with pytest.raises(InvalidApiKeyError):
        authenticate_api_key(
            session=session,
            api_key=f"{generated.key_prefix}.wrong-secret",
            pepper=TEST_PEPPER,
        )
