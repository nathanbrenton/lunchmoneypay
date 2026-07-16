"""Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.authentication import router as authentication_router
from app.api.v1.customers import router as customers_router
from app.api.v1.health import router as health_router
from app.api.v1.merchant_api_credentials import (
    router as merchant_api_credentials_router,
)
from app.api.v1.merchants import router as merchants_router
from app.api.v1.payment_events import router as payment_events_router
from app.api.v1.payment_intents import router as payment_intents_router
from app.api.v1.payment_methods import router as payment_methods_router
from app.api.v1.refunds import router as refunds_router
from app.api.v1.webhooks import delivery_router as webhook_deliveries_router
from app.api.v1.webhooks import router as webhook_endpoints_router
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(authentication_router)
api_router.include_router(customers_router)
api_router.include_router(health_router)
api_router.include_router(merchants_router)
api_router.include_router(payment_events_router)
api_router.include_router(payment_intents_router)
api_router.include_router(payment_methods_router)
api_router.include_router(refunds_router)
api_router.include_router(webhook_endpoints_router)
api_router.include_router(webhook_deliveries_router)
api_router.include_router(merchant_api_credentials_router)
