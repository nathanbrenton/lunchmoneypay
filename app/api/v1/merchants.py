"""Merchant API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantRead
from app.services.exceptions import (
    MerchantAlreadyExistsError,
    MerchantNotFoundError,
)
from app.services.merchant import create_merchant, get_merchant

router = APIRouter(
    prefix="/merchants",
    tags=["merchants"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]


@router.post(
    "",
    response_model=MerchantRead,
    status_code=status.HTTP_201_CREATED,
)
def create_merchant_endpoint(
    merchant_create: MerchantCreate,
    session: DatabaseSession,
) -> Merchant:
    """Create a merchant account."""

    try:
        return create_merchant(
            session=session,
            merchant_create=merchant_create,
        )
    except MerchantAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A merchant with this name already exists.",
        ) from exc


@router.get(
    "/{merchant_id}",
    response_model=MerchantRead,
)
def get_merchant_endpoint(
    merchant_id: uuid.UUID,
    session: DatabaseSession,
) -> Merchant:
    """Return a merchant by processor-side UUID."""

    try:
        return get_merchant(
            session=session,
            merchant_id=merchant_id,
        )
    except MerchantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found.",
        ) from exc
