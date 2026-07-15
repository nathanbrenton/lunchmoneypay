"""Business logic for merchant operations."""

from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate


def create_merchant(
    session: Session,
    merchant_create: MerchantCreate,
) -> Merchant:
    """Create and persist a merchant."""

    merchant = Merchant(
        name=merchant_create.name,
    )

    session.add(merchant)
    session.flush()
    session.refresh(merchant)

    return merchant
