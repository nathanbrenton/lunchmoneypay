"""Tests for merchant API credential schemas."""

import uuid
from datetime import UTC, datetime

from app.schemas.merchant_api_credential import (
    MerchantApiCredentialCreated,
    MerchantApiCredentialRead,
)


def test_credential_read_accepts_safe_metadata() -> None:
    credential_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)

    credential = MerchantApiCredentialRead(
        id=credential_id,
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        status="active",
        expires_at=None,
        created_at=timestamp,
    )

    assert credential.id == credential_id
    assert credential.merchant_id == merchant_id
    assert credential.key_prefix == "lmp_test_a1b2c3d4e5f6"
    assert not hasattr(credential, "secret_hash")
    assert not hasattr(credential, "api_key")


def test_credential_created_includes_one_time_api_key() -> None:
    credential_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    timestamp = datetime.now(UTC)
    api_key = "lmp_test_a1b2c3d4e5f6.example-secret"

    credential = MerchantApiCredentialCreated(
        id=credential_id,
        merchant_id=merchant_id,
        key_prefix="lmp_test_a1b2c3d4e5f6",
        status="active",
        expires_at=None,
        created_at=timestamp,
        api_key=api_key,
    )

    assert credential.api_key == api_key
    assert not hasattr(credential, "secret_hash")
