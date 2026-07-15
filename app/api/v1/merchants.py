"""Merchant API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantRead
from app.services.exceptions import MerchantAlreadyExistsError
from app.services.merchant import create_merchant

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
