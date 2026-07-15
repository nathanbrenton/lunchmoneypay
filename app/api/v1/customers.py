"""Customer API endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthenticatedCredential, DatabaseSession
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerRead
from app.services.customer import create_customer
from app.services.exceptions import CustomerAlreadyExistsError

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_endpoint(
    customer_create: CustomerCreate,
    credential: AuthenticatedCredential,
    session: DatabaseSession,
) -> Customer:
    """Create a customer for the authenticated merchant."""

    try:
        return create_customer(
            session=session,
            merchant_id=credential.merchant_id,
            customer_create=customer_create,
        )
    except CustomerAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A customer with this external reference "
                "already exists for this merchant."
            ),
        ) from exc
