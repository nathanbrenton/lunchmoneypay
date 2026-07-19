"""Tests for application configuration."""

from app.core.config import Settings


def test_settings_use_expected_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "LunchMoneyPay"
    assert settings.app_version == "0.3.0"
    assert settings.app_environment == "development"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.api_key_pepper == "development-only-change-me"
    assert settings.database_url == (
        "postgresql+psycopg://lunchmoneypay:lunchmoneypay@127.0.0.1:18533/lunchmoneypay"
    )


def test_production_rejects_demo_checkout() -> None:
    import pytest

    with pytest.raises(ValueError, match="demo checkout flow"):
        Settings(
            _env_file=None,
            app_environment="production",
            canonical_public_origin="https://pay.example.com",
            api_key_pepper="p" * 32,
            demo_checkout_enabled=True,
        )


def test_production_accepts_disabled_demo_checkout() -> None:
    settings = Settings(
        _env_file=None,
        app_environment="production",
        canonical_public_origin="https://pay.example.com",
        api_key_pepper="p" * 32,
        demo_checkout_enabled=False,
    )

    assert settings.demo_checkout_enabled is False
