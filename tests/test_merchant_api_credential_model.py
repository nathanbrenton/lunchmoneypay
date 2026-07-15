"""Tests for the merchant API credential model."""

from app.models.merchant_api_credential import MerchantApiCredential


def test_merchant_api_credential_uses_expected_table_name() -> None:
    assert MerchantApiCredential.__tablename__ == "merchant_api_credentials"


def test_merchant_api_credential_accepts_expected_attributes() -> None:
    credential = MerchantApiCredential(
        key_prefix="lmp_live_ab12",
        secret_hash="hashed-secret-value",
        status="active",
    )

    assert credential.key_prefix == "lmp_live_ab12"
    assert credential.secret_hash == "hashed-secret-value"
    assert credential.status == "active"


def test_merchant_api_credential_contains_expected_columns() -> None:
    assert set(MerchantApiCredential.__table__.columns.keys()) == {
        "id",
        "merchant_id",
        "key_prefix",
        "secret_hash",
        "status",
        "expires_at",
        "created_at",
    }


def test_merchant_api_credential_prefix_is_unique() -> None:
    column = MerchantApiCredential.__table__.columns["key_prefix"]

    assert column.unique is True


def test_merchant_api_credential_defines_expected_defaults() -> None:
    columns = MerchantApiCredential.__table__.columns

    assert columns["id"].default is not None
    assert columns["status"].default is not None
    assert columns["created_at"].server_default is not None
