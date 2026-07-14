"""LunchMoneyPay FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="LunchMoneyPay",
    version="0.1.0",
    description=(
        "A mock payment-processing service for service-to-service "
        "integration development."
    ),
)


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    """Return a simple service status message."""
    return {"message": "LunchMoneyPay is running"}


app.include_router(api_router)
