"""Business logic for merchant operations."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate
from app.services.exceptions import MerchantAlreadyExistsError


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
