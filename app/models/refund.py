"""Refund database model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Refund(Base):
    """A merchant-scoped refund against a succeeded payment intent."""

    __tablename__ = "refunds"

    __table_args__ = (
        CheckConstraint(
            "amount_minor > 0",
            name="ck_refunds_amount_positive",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_refunds_currency_format",
        ),
        CheckConstraint(
            "status IN ('succeeded')",
            name="ck_refunds_status",
        ),
        UniqueConstraint(
            "merchant_id",
            "external_reference",
            name="uq_refunds_merchant_external_reference",
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

    payment_intent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_intents.id"),
        nullable=False,
    )

    external_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    amount_minor: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        default="succeeded",
        server_default="succeeded",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
