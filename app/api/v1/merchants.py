"""Merchant API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantRead
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

    return create_merchant(
        session=session,
        merchant_create=merchant_create,
    )
