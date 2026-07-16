"""Tests for refund persistence."""

import uuid

from app.models.refund import Refund


def test_refund_uses_expected_table_name() -> None:
    """Store refunds in a dedicated table."""

    assert Refund.__tablename__ == "refunds"


def test_refund_has_merchant_and_payment_intent_identity() -> None:
    """Associate refunds with their merchant and payment intent."""

    merchant_id = uuid.uuid4()
    payment_intent_id = uuid.uuid4()

    refund = Refund(
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        external_reference="refund-123",
        amount_minor=1000,
        currency="USD",
    )

    assert refund.merchant_id == merchant_id
    assert refund.payment_intent_id == payment_intent_id
    assert refund.amount_minor == 1000


def test_refund_has_expected_constraints() -> None:
    """Protect refund amount, state, currency, and merchant reference."""

    constraint_names = {
        constraint.name
        for constraint in Refund.__table__.constraints
        if constraint.name is not None
    }

    assert "ck_refunds_amount_positive" in constraint_names
    assert "ck_refunds_currency_format" in constraint_names
    assert "ck_refunds_status" in constraint_names
    assert "uq_refunds_merchant_external_reference" in constraint_names
