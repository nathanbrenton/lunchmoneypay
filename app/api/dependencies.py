"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.merchant_api_credential import MerchantApiCredential
from app.services.api_authentication import authenticate_api_key
from app.services.exceptions import (
    InactiveApiCredentialError,
    InvalidApiKeyError,
)

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="MerchantApiKey",
    description="LunchMoneyPay service-to-service merchant API key.",
    auto_error=False,
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]

PresentedApiKey = Annotated[
    str | None,
    Depends(api_key_header),
]


def get_authenticated_credential(
    session: DatabaseSession,
    api_key: PresentedApiKey,
) -> MerchantApiCredential:
    """Return the authenticated merchant API credential."""

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required.",
        )

    settings = get_settings()

    try:
        return authenticate_api_key(
            session=session,
            api_key=api_key,
            pepper=settings.api_key_pepper,
        )
    except InvalidApiKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        ) from exc
    except InactiveApiCredentialError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


AuthenticatedCredential = Annotated[
    MerchantApiCredential,
    Depends(get_authenticated_credential),
]
