from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LunchMoneyPay"
    app_env: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    host: str = "127.0.0.1"
    port: int = 9000

    database_url: str = Field(
        default="postgresql+psycopg://lunchmoneypay:lunchmoneypay_dev_password@127.0.0.1:5432/lunchmoneypay_dev"
    )

    secret_key: str = "dev-only-change-me"
    webhook_signing_secret: str = "dev-webhook-secret-change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
