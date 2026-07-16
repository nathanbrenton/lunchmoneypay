"""Tests for idempotency-record persistence."""

from app.models.idempotency_record import IdempotencyRecord


def test_idempotency_record_uses_expected_table_and_constraint() -> None:
    """Persist one merchant-scoped record per idempotency key."""

    constraint_names = {
        constraint.name
        for constraint in IdempotencyRecord.__table__.constraints
        if constraint.name is not None
    }

    assert IdempotencyRecord.__tablename__ == "idempotency_records"
    assert "uq_idempotency_records_merchant_key" in constraint_names
