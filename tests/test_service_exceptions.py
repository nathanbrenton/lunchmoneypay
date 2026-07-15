"""Tests for LunchMoneyPay service exceptions."""

from app.services.exceptions import (
    InactiveApiCredentialError,
    InvalidApiKeyError,
)


def test_invalid_api_key_error_is_an_exception() -> None:
    error = InvalidApiKeyError("invalid credential")

    assert isinstance(error, Exception)
    assert str(error) == "invalid credential"


def test_inactive_api_credential_error_is_an_exception() -> None:
    error = InactiveApiCredentialError("revoked credential")

    assert isinstance(error, Exception)
    assert str(error) == "revoked credential"


def test_authentication_exceptions_are_distinct() -> None:
    assert InvalidApiKeyError is not InactiveApiCredentialError
