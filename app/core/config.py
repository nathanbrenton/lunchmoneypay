"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for LunchMoneyPay."""

    app_name: str = "LunchMoneyPay"
    app_version: str = "0.1.0"
    app_environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    api_key_pepper: str = "development-only-change-me"
    database_url: str = (
        "postgresql+psycopg://lunchmoneypay:lunchmoneypay@127.0.0.1:5432/lunchmoneypay"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
