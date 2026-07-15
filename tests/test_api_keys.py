"""Tests for merchant API key security utilities."""

import pytest

from app.core.api_keys import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
)

TEST_PEPPER = "development-only-test-pepper"


def test_generate_api_key_returns_expected_format() -> None:
    generated = generate_api_key(TEST_PEPPER)

    prefix, secret = generated.api_key.split(".", maxsplit=1)

    assert prefix == generated.key_prefix
    assert prefix.startswith("lmp_test_")
    assert len(secret) > 32
    assert generated.secret_hash != generated.api_key


def test_generate_api_key_returns_unique_credentials() -> None:
    first = generate_api_key(TEST_PEPPER)
    second = generate_api_key(TEST_PEPPER)

    assert first.api_key != second.api_key
    assert first.key_prefix != second.key_prefix
    assert first.secret_hash != second.secret_hash


def test_generate_api_key_rejects_empty_pepper() -> None:
    with pytest.raises(
        ValueError,
        match="API key pepper must not be empty",
    ):
        generate_api_key("")


def test_hash_api_key_is_deterministic() -> None:
    api_key = "lmp_test_123456789abc.example-secret"

    assert hash_api_key(api_key, TEST_PEPPER) == hash_api_key(
        api_key,
        TEST_PEPPER,
    )


def test_verify_api_key_accepts_matching_key() -> None:
    generated = generate_api_key(TEST_PEPPER)

    assert verify_api_key(
        generated.api_key,
        generated.secret_hash,
        TEST_PEPPER,
    )


def test_verify_api_key_rejects_wrong_key() -> None:
    generated = generate_api_key(TEST_PEPPER)

    assert not verify_api_key(
        f"{generated.key_prefix}.wrong-secret",
        generated.secret_hash,
        TEST_PEPPER,
    )


def test_verify_api_key_rejects_wrong_pepper() -> None:
    generated = generate_api_key(TEST_PEPPER)

    assert not verify_api_key(
        generated.api_key,
        generated.secret_hash,
        "different-pepper",
    )
