"""API-key authentication verification endpoints."""

from fastapi import APIRouter

from app.api.dependencies import AuthenticatedCredential
from app.schemas.authentication import AuthenticatedMerchantContext

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.get(
    "/whoami",
    response_model=AuthenticatedMerchantContext,
)
def read_authenticated_context(
    credential: AuthenticatedCredential,
) -> AuthenticatedMerchantContext:
    """Return safe context for the authenticated merchant credential."""

    return AuthenticatedMerchantContext(
        merchant_id=credential.merchant_id,
        credential_id=credential.id,
        key_prefix=credential.key_prefix,
    )
