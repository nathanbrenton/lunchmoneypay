"""Authentication logic for merchant API credentials."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.api_keys import verify_api_key
from app.models.merchant_api_credential import MerchantApiCredential
from app.services.exceptions import (
    InactiveApiCredentialError,
    InvalidApiKeyError,
)


def extract_key_prefix(api_key: str) -> str:
    """Return the public prefix from a complete API key."""

    key_prefix, separator, secret = api_key.partition(".")

    if not separator or not key_prefix.startswith("lmp_") or not secret:
        raise InvalidApiKeyError("Invalid API key.")

    return key_prefix


def authenticate_api_key(
    session: Session,
    api_key: str,
    pepper: str,
) -> MerchantApiCredential:
    """Authenticate an API key and return its credential record."""

    key_prefix = extract_key_prefix(api_key)

    statement = select(MerchantApiCredential).where(
        MerchantApiCredential.key_prefix == key_prefix
    )

    credential = session.scalar(statement)

    if credential is None:
        raise InvalidApiKeyError("Invalid API key.")

    if not verify_api_key(
        api_key=api_key,
        expected_hash=credential.secret_hash,
        pepper=pepper,
    ):
        raise InvalidApiKeyError("Invalid API key.")

    if credential.status != "active":
        raise InactiveApiCredentialError("API credential is not active.")

    if credential.expires_at is not None and credential.expires_at <= datetime.now(UTC):
        raise InactiveApiCredentialError("API credential has expired.")

    return credential
