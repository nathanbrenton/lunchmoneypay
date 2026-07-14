"""Health-check and readiness API endpoints."""

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.db.checks import database_is_ready

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health() -> dict[str, str]:
    """Report application-process health without external checks."""

    settings = get_settings()

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_environment,
    }


@router.get("/ready")
def read_readiness(response: Response) -> dict[str, str]:
    """Report whether required database connectivity is available."""

    if not database_is_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "not_ready",
            "database": "unavailable",
        }

    return {
        "status": "ready",
        "database": "available",
    }
