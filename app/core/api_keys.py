"""Secure generation and verification of merchant API keys."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass

KEY_ENVIRONMENT = "test"
PREFIX_RANDOM_BYTES = 6
SECRET_RANDOM_BYTES = 32


@dataclass(frozen=True)
class GeneratedApiKey:
    """A newly generated API key and its safe storage values."""

    api_key: str
    key_prefix: str
    secret_hash: str


def hash_api_key(
    api_key: str,
    pepper: str,
) -> str:
    """Return a keyed SHA-256 digest for an API key."""

    return hmac.new(
        key=pepper.encode("utf-8"),
        msg=api_key.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def generate_api_key(
    pepper: str,
) -> GeneratedApiKey:
    """Generate a new test API key and its storage-safe values."""

    if not pepper:
        raise ValueError("API key pepper must not be empty.")

    random_prefix = secrets.token_hex(PREFIX_RANDOM_BYTES)
    key_prefix = f"lmp_{KEY_ENVIRONMENT}_{random_prefix}"

    secret = secrets.token_urlsafe(SECRET_RANDOM_BYTES)
    api_key = f"{key_prefix}.{secret}"

    return GeneratedApiKey(
        api_key=api_key,
        key_prefix=key_prefix,
        secret_hash=hash_api_key(api_key, pepper),
    )


def verify_api_key(
    api_key: str,
    expected_hash: str,
    pepper: str,
) -> bool:
    """Return whether an API key matches its stored digest."""

    actual_hash = hash_api_key(api_key, pepper)

    return hmac.compare_digest(
        actual_hash,
        expected_hash,
    )
