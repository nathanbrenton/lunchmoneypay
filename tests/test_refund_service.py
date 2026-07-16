"""Tests for refund service operations."""

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

import app.services.refund as refund_service
from app.models.payment_intent import PaymentIntent
from app.models.refund import Refund
from app.schemas.refund import RefundCreate
from app.services.exceptions import (
    PaymentIntentNotRefundableError,
    RefundAmountExceedsAvailableError,
    RefundNotFoundError,
)


def build_succeeded_payment_intent(
    merchant_id: uuid.UUID,
    payment_intent_id: uuid.UUID,
) -> PaymentIntent:
    """Build a refundable payment intent."""

    return PaymentIntent(
        id=payment_intent_id,
        merchant_id=merchant_id,
        customer_id=uuid.uuid4(),
        external_reference="payment-123",
        amount_minor=2500,
        currency="USD",
        status="succeeded",
    )


def test_create_refund_records_partial_refund_and_event(
    monkeypatch,
) -> None:
    """Create a partial refund and its durable lifecycle event."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_intent = build_succeeded_payment_intent(
        merchant_id,
        payment_intent_id,
    )

    monkeypatch.setattr(
        refund_service,
        "get_payment_intent",
        lambda **kwargs: payment_intent,
    )

    session.scalar.return_value = 500
    recorded_event = {}

    def fake_create_refund_event(
        session,
        refund,
        payment_intent,
    ):
        recorded_event["refund"] = refund
        recorded_event["payment_intent"] = payment_intent

    monkeypatch.setattr(
        refund_service,
        "create_refund_event",
        fake_create_refund_event,
    )

    result = refund_service.create_refund(
        session=session,
        merchant_id=merchant_id,
        refund_create=RefundCreate(
            payment_intent_id=payment_intent_id,
            external_reference="refund-123",
            amount_minor=1000,
        ),
    )

    assert result.merchant_id == merchant_id
    assert result.payment_intent_id == payment_intent_id
    assert result.amount_minor == 1000
    assert result.currency == "USD"
    assert result.status == "succeeded"
    assert recorded_event == {
        "refund": result,
        "payment_intent": payment_intent,
    }

    session.add.assert_called_once_with(result)
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(result)


def test_create_refund_rejects_non_succeeded_payment(
    monkeypatch,
) -> None:
    """Reject refunds for payments that have not succeeded."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_intent = build_succeeded_payment_intent(
        merchant_id,
        payment_intent_id,
    )
    payment_intent.status = "requires_payment_method"

    monkeypatch.setattr(
        refund_service,
        "get_payment_intent",
        lambda **kwargs: payment_intent,
    )

    with pytest.raises(PaymentIntentNotRefundableError):
        refund_service.create_refund(
            session=session,
            merchant_id=merchant_id,
            refund_create=RefundCreate(
                payment_intent_id=payment_intent_id,
                external_reference="refund-123",
                amount_minor=1000,
            ),
        )

    session.commit.assert_not_called()


def test_create_refund_rejects_amount_above_remaining_balance(
    monkeypatch,
) -> None:
    """Reject refunds exceeding the remaining refundable amount."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    payment_intent = build_succeeded_payment_intent(
        merchant_id,
        payment_intent_id,
    )

    monkeypatch.setattr(
        refund_service,
        "get_payment_intent",
        lambda **kwargs: payment_intent,
    )

    session.scalar.return_value = 2000

    with pytest.raises(RefundAmountExceedsAvailableError):
        refund_service.create_refund(
            session=session,
            merchant_id=merchant_id,
            refund_create=RefundCreate(
                payment_intent_id=payment_intent_id,
                external_reference="refund-123",
                amount_minor=1000,
            ),
        )


def test_get_refund_returns_merchant_owned_record() -> None:
    """Retrieve a refund within the merchant boundary."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    refund_id = uuid.uuid4()

    refund = Refund(
        id=refund_id,
        merchant_id=merchant_id,
        payment_intent_id=uuid.uuid4(),
        external_reference="refund-123",
        amount_minor=1000,
        currency="USD",
        status="succeeded",
    )
    session.get.return_value = refund

    result = refund_service.get_refund(
        session=session,
        merchant_id=merchant_id,
        refund_id=refund_id,
    )

    assert result is refund


def test_get_refund_rejects_other_merchant_record() -> None:
    """Hide refunds owned by another merchant."""

    session = MagicMock(spec=Session)
    refund_id = uuid.uuid4()

    session.get.return_value = Refund(
        id=refund_id,
        merchant_id=uuid.uuid4(),
        payment_intent_id=uuid.uuid4(),
        external_reference="refund-123",
        amount_minor=1000,
        currency="USD",
        status="succeeded",
    )

    with pytest.raises(RefundNotFoundError):
        refund_service.get_refund(
            session=session,
            merchant_id=uuid.uuid4(),
            refund_id=refund_id,
        )


def test_list_refunds_filters_by_merchant_and_payment_intent() -> None:
    """List newest refunds for one merchant payment intent."""

    session = MagicMock(spec=Session)
    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()
    refund = Refund(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        external_reference="refund-123",
        amount_minor=1000,
        currency="USD",
        status="succeeded",
    )

    session.scalars.return_value.all.return_value = [refund]

    result = refund_service.list_refunds(
        session=session,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    assert result == [refund]

    statement = session.scalars.call_args.args[0]
    compiled = str(
        statement.compile(
            compile_kwargs={"literal_binds": True},
        )
    )

    assert merchant_id.hex in compiled
    assert payment_intent_id.hex in compiled
    assert "refunds.created_at DESC" in compiled
