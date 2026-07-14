"""LunchMoneyPay FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A mock payment-processing service for service-to-service "
        "integration development."
    ),
)


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    """Return a simple service status message."""

    return {"message": f"{settings.app_name} is running"}


app.include_router(api_router)
