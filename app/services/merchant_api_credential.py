"""Business logic for merchant API credentials."""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.api_keys import generate_api_key
from app.models.merchant_api_credential import MerchantApiCredential


@dataclass(frozen=True)
class CreatedMerchantApiCredential:
    """A persisted credential and its one-time plaintext API key."""

    credential: MerchantApiCredential
    api_key: str


def create_merchant_api_credential(
    session: Session,
    merchant_id: uuid.UUID,
    pepper: str,
) -> CreatedMerchantApiCredential:
    """Create and persist a merchant API credential."""

    generated = generate_api_key(pepper)

    credential = MerchantApiCredential(
        merchant_id=merchant_id,
        key_prefix=generated.key_prefix,
        secret_hash=generated.secret_hash,
    )

    session.add(credential)
    session.commit()
    session.refresh(credential)

    return CreatedMerchantApiCredential(
        credential=credential,
        api_key=generated.api_key,
    )
