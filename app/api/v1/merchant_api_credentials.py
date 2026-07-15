"""Merchant API credential endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.merchant_api_credential import MerchantApiCredential
from app.schemas.merchant_api_credential import MerchantApiCredentialCreated
from app.services.exceptions import MerchantNotFoundError
from app.services.merchant_api_credential import (
    CreatedMerchantApiCredential,
    create_merchant_api_credential,
)

router = APIRouter(
    prefix="/merchants/{merchant_id}/credentials",
    tags=["merchant credentials"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]


@router.post(
    "",
    response_model=MerchantApiCredentialCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_merchant_api_credential_endpoint(
    merchant_id: uuid.UUID,
    session: DatabaseSession,
) -> MerchantApiCredentialCreated:
    """Create an API credential and return its secret once."""

    settings = get_settings()

    try:
        created = create_merchant_api_credential(
            session=session,
            merchant_id=merchant_id,
            pepper=settings.api_key_pepper,
        )
    except MerchantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found.",
        ) from exc

    return build_created_response(created)


def build_created_response(
    created: CreatedMerchantApiCredential,
) -> MerchantApiCredentialCreated:
    """Build the one-time credential creation response."""

    credential: MerchantApiCredential = created.credential

    return MerchantApiCredentialCreated(
        id=credential.id,
        merchant_id=credential.merchant_id,
        key_prefix=credential.key_prefix,
        status=credential.status,
        expires_at=credential.expires_at,
        created_at=credential.created_at,
        api_key=created.api_key,
    )
