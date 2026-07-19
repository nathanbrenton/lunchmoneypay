"""Bounded demo checkout orchestration for service integration testing."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.payment_intent import PaymentIntent
from app.models.payment_method import PaymentMethod
from app.schemas.checkout_session import DemoCheckoutSessionCreate
from app.schemas.customer import CustomerCreate
from app.schemas.payment_intent import PaymentIntentCreate
from app.schemas.payment_method import PaymentMethodCreate
from app.services.customer import create_customer
from app.services.exceptions import CustomerAlreadyExistsError
from app.services.idempotency import (
    create_idempotency_record,
    get_idempotency_record,
    hash_request_payload,
    validate_idempotency_replay,
)
from app.services.payment_intent import (
    attach_payment_method,
    confirm_payment_intent,
    create_payment_intent,
    get_payment_intent,
)
from app.services.payment_method import create_payment_method

CHECKOUT_OPERATION = "checkout_session.create"
CHECKOUT_RESOURCE_TYPE = "payment_intent"


@dataclass(frozen=True)
class DemoCheckoutResult:
    """Internal response carrying only bounded display metadata."""

    payment_intent: PaymentIntent
    payment_method: PaymentMethod


def _get_or_create_customer(
    session: Session,
    *,
    merchant_id: uuid.UUID,
    payload: DemoCheckoutSessionCreate,
) -> Customer:
    customer = session.scalar(
        select(Customer).where(
            Customer.merchant_id == merchant_id,
            Customer.external_reference == payload.customer_external_reference,
        )
    )
    if customer is not None:
        return customer

    try:
        return create_customer(
            session=session,
            merchant_id=merchant_id,
            customer_create=CustomerCreate(
                external_reference=payload.customer_external_reference,
                display_name=payload.customer_display_name,
                email=payload.customer_email,
            ),
        )
    except CustomerAlreadyExistsError:
        # A concurrent request may have created the same merchant customer.
        customer = session.scalar(
            select(Customer).where(
                Customer.merchant_id == merchant_id,
                Customer.external_reference == payload.customer_external_reference,
            )
        )
        if customer is None:
            raise
        return customer


def _safe_mock_method_values(test_scenario: str) -> tuple[str, str]:
    if test_scenario == "card_declined":
        return ("visa", "0002")
    return ("visa", "4242")


def _load_terminal_result(
    session: Session,
    *,
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID,
) -> DemoCheckoutResult:
    payment_intent = get_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )
    if payment_intent.status not in {"succeeded", "failed"}:
        raise RuntimeError("Persisted checkout is not in a terminal state.")
    if payment_intent.payment_method_id is None:
        raise RuntimeError("Persisted checkout has no payment method.")

    payment_method = session.get(PaymentMethod, payment_intent.payment_method_id)
    if payment_method is None or payment_method.merchant_id != merchant_id:
        raise RuntimeError("Persisted payment method is unavailable.")

    return DemoCheckoutResult(
        payment_intent=payment_intent,
        payment_method=payment_method,
    )


def _internal_payment_intent_key(idempotency_key: str) -> str:
    """Derive a separate stable key for the lower-level create operation."""

    digest = hashlib.sha256(idempotency_key.encode()).hexdigest()
    return f"checkout-intent:{digest}"


def create_demo_checkout_session(
    session: Session,
    *,
    merchant_id: uuid.UUID,
    payload: DemoCheckoutSessionCreate,
    idempotency_key: str,
    expiration_year: int,
) -> DemoCheckoutResult:
    """Create, attach, and confirm a demo payment without accepting card data."""

    request_hash = hash_request_payload(payload)
    existing_record = get_idempotency_record(
        session=session,
        merchant_id=merchant_id,
        idempotency_key=idempotency_key,
    )
    if existing_record is not None:
        validate_idempotency_replay(
            record=existing_record,
            operation=CHECKOUT_OPERATION,
            request_hash=request_hash,
            resource_type=CHECKOUT_RESOURCE_TYPE,
        )
        return _load_terminal_result(
            session,
            merchant_id=merchant_id,
            payment_intent_id=existing_record.resource_id,
        )

    customer = _get_or_create_customer(
        session,
        merchant_id=merchant_id,
        payload=payload,
    )

    payment_intent = create_payment_intent(
        session=session,
        merchant_id=merchant_id,
        payment_intent_create=PaymentIntentCreate(
            customer_id=customer.id,
            external_reference=payload.external_reference,
            amount_minor=payload.amount_minor,
            currency=payload.currency,
        ),
        idempotency_key=_internal_payment_intent_key(idempotency_key),
    )

    if payment_intent.payment_method_id is not None:
        payment_method = session.get(PaymentMethod, payment_intent.payment_method_id)
        if payment_method is None or payment_method.merchant_id != merchant_id:
            raise RuntimeError("Persisted payment method is unavailable.")
    else:
        brand, last4 = _safe_mock_method_values(payload.test_scenario)
        payment_method = create_payment_method(
            session=session,
            merchant_id=merchant_id,
            payment_method_create=PaymentMethodCreate(
                customer_id=customer.id,
                card_brand=brand,
                card_last4=last4,
                card_exp_month=12,
                card_exp_year=expiration_year,
                test_scenario=payload.test_scenario,
            ),
        )
        payment_intent = attach_payment_method(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent.id,
            payment_method_id=payment_method.id,
        )

    if payment_intent.status == "requires_payment_method":
        payment_intent = confirm_payment_intent(
            session=session,
            merchant_id=merchant_id,
            payment_intent_id=payment_intent.id,
        )

    if payment_intent.status not in {"succeeded", "failed"}:
        raise RuntimeError("Demo checkout did not reach a terminal state.")

    session.add(
        create_idempotency_record(
            merchant_id=merchant_id,
            idempotency_key=idempotency_key,
            operation=CHECKOUT_OPERATION,
            request_hash=request_hash,
            resource_type=CHECKOUT_RESOURCE_TYPE,
            resource_id=payment_intent.id,
        )
    )
    try:
        session.commit()
    except IntegrityError:
        # A concurrent identical request may have completed the outer record.
        session.rollback()
        existing_record = get_idempotency_record(
            session=session,
            merchant_id=merchant_id,
            idempotency_key=idempotency_key,
        )
        if existing_record is None:
            raise
        validate_idempotency_replay(
            record=existing_record,
            operation=CHECKOUT_OPERATION,
            request_hash=request_hash,
            resource_type=CHECKOUT_RESOURCE_TYPE,
        )
        return _load_terminal_result(
            session,
            merchant_id=merchant_id,
            payment_intent_id=existing_record.resource_id,
        )

    return DemoCheckoutResult(
        payment_intent=payment_intent,
        payment_method=payment_method,
    )
