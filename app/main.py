from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Mock third-party payment processor for Homesteady ChoreTracker.",
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/")
def read_root():
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
        "message": "Mock payment processor API is online.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
    }
