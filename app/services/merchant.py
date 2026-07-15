"""Business logic for merchant operations."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate
from app.services.exceptions import (
    MerchantAlreadyExistsError,
    MerchantNotFoundError,
)


def create_merchant(
    session: Session,
    merchant_create: MerchantCreate,
) -> Merchant:
    """Create and persist a merchant."""

    merchant = Merchant(
        name=merchant_create.name,
    )

    session.add(merchant)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise MerchantAlreadyExistsError(merchant_create.name) from exc

    session.refresh(merchant)

    return merchant


def get_merchant(
    session: Session,
    merchant_id: uuid.UUID,
) -> Merchant:
    """Return a merchant by its processor-side UUID."""

    merchant = session.get(Merchant, merchant_id)

    if merchant is None:
        raise MerchantNotFoundError(merchant_id)

    return merchant
