"""Tests for application configuration."""

from app.core.config import Settings


def test_settings_use_expected_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "LunchMoneyPay"
    assert settings.app_version == "0.1.0"
    assert settings.app_environment == "development"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.database_url == (
        "postgresql+psycopg://lunchmoneypay:lunchmoneypay@127.0.0.1:5432/lunchmoneypay"
    )
