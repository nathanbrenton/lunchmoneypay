"""Mock payment-method database model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentMethod(Base):
    """A merchant-scoped reusable mock payment method."""

    __tablename__ = "payment_methods"

    __table_args__ = (
        CheckConstraint(
            "type IN ('card')",
            name="ck_payment_methods_type",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_payment_methods_status",
        ),
        CheckConstraint(
            "test_scenario IN ('success', 'card_declined')",
            name="ck_payment_methods_test_scenario",
        ),
        CheckConstraint(
            "card_exp_month BETWEEN 1 AND 12",
            name="ck_payment_methods_card_exp_month",
        ),
        CheckConstraint(
            "card_last4 ~ '^[0-9]{4}$'",
            name="ck_payment_methods_card_last4_format",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("merchants.id"),
        nullable=False,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    card_brand: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    card_last4: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )

    card_exp_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    card_exp_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        server_default="active",
        nullable=False,
    )

    test_scenario: Mapped[str] = mapped_column(
        String(50),
        default="success",
        server_default="success",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
