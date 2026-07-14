"""Health-check API endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def read_health() -> dict[str, str]:
    """Report the current application health."""
    return {
        "status": "ok",
        "service": "LunchMoneyPay",
    }
