"""Health-check API endpoints."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def read_health() -> dict[str, str]:
    """Report the current application health."""

    settings = get_settings()

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_environment,
    }
