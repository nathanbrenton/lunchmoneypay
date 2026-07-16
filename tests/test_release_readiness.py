"""Release-readiness checks for the ChoreTracker integration MVP."""

from pathlib import Path

from app.core.config import get_settings
from app.main import app

EXPECTED_ROUTES = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/ready"),
    ("GET", "/api/v1/auth/whoami"),
    ("POST", "/api/v1/customers"),
    ("POST", "/api/v1/payment-methods"),
    ("POST", "/api/v1/payment-intents"),
    ("POST", "/api/v1/payment-intents/{payment_intent_id}/confirm"),
    ("POST", "/api/v1/refunds"),
    ("POST", "/api/v1/webhook-endpoints"),
    (
        "POST",
        "/api/v1/webhook-deliveries/{webhook_delivery_id}/retry",
    ),
}


def test_integration_routes_are_registered() -> None:
    """Expose every route required by the initial ChoreTracker client."""

    openapi_paths = app.openapi()["paths"]

    registered = {
        (method.upper(), path)
        for path, operations in openapi_paths.items()
        for method in operations
        if method.upper()
        in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }
    }

    assert EXPECTED_ROUTES <= registered


def test_openapi_exposes_merchant_api_key_scheme() -> None:
    """Document the merchant API-key header in OpenAPI."""

    security_schemes = app.openapi()["components"]["securitySchemes"]

    assert security_schemes["MerchantApiKey"] == {
        "type": "apiKey",
        "description": ("LunchMoneyPay service-to-service merchant API key."),
        "in": "header",
        "name": "X-API-Key",
    }


def test_release_version_is_consistent() -> None:
    """Keep application and package release versions aligned."""

    settings = get_settings()
    pyproject = Path("pyproject.toml").read_text()

    assert settings.app_version == "0.2.0"
    assert 'version = "0.2.0"' in pyproject
