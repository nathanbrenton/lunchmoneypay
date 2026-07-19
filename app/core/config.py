"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _validate_origin(value: str, *, field_name: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{field_name} must be an absolute HTTP(S) origin.")
    if parsed.username or parsed.password:
        raise ValueError(f"{field_name} must not include user information.")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError(f"{field_name} must not include a path, query, or fragment.")


class Settings(BaseSettings):
    """Runtime settings for LunchMoneyPay."""

    app_name: str = "LunchMoneyPay"
    app_version: str = "0.3.0"
    app_environment: Literal["development", "test", "staging", "production"] = (
        "development"
    )
    api_v1_prefix: str = "/api/v1"
    canonical_public_origin: str = "http://127.0.0.1:18531"
    api_key_pepper: str = "development-only-change-me"
    database_url: str = (
        "postgresql+psycopg://lunchmoneypay:lunchmoneypay@127.0.0.1:18533/lunchmoneypay"
    )
    demo_checkout_enabled: bool = True
    demo_checkout_expiration_year: int = Field(default=2099, ge=2030, le=9999)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if not self.api_v1_prefix.startswith("/"):
            raise ValueError("API_V1_PREFIX must begin with '/'.")
        _validate_origin(
            self.canonical_public_origin,
            field_name="CANONICAL_PUBLIC_ORIGIN",
        )

        if self.app_environment in {"staging", "production"}:
            if not self.canonical_public_origin.startswith("https://"):
                raise ValueError(
                    "LunchMoneyPay canonical origin must use HTTPS outside "
                    "development and test."
                )
            if self.demo_checkout_enabled:
                raise ValueError(
                    "The fixed demo checkout flow must be disabled outside "
                    "development and test."
                )
            if (
                self.api_key_pepper == "development-only-change-me"
                or len(self.api_key_pepper) < 32
            ):
                raise ValueError(
                    "A non-placeholder API key pepper of at least 32 characters "
                    "is required outside development and test."
                )

        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
