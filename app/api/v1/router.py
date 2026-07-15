"""Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.authentication import router as authentication_router
from app.api.v1.health import router as health_router
from app.api.v1.merchant_api_credentials import (
    router as merchant_api_credentials_router,
)
from app.api.v1.merchants import router as merchants_router
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(authentication_router)
api_router.include_router(health_router)
api_router.include_router(merchants_router)
api_router.include_router(merchant_api_credentials_router)
