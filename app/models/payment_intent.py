"""Payment-intent database model."""

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


class PaymentIntent(Base):
    """A merchant-scoped request to collect a payment."""

    __tablename__ = "payment_intents"

    __table_args__ = (
        CheckConstraint(
            "status IN ('requires_payment_method', 'processing', "
            "'succeeded', 'canceled')",
            name="ck_payment_intents_status",
        ),
        CheckConstraint(
            "amount_minor > 0",
            name="ck_payment_intents_amount_positive",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_payment_intents_currency_format",
        ),
        UniqueConstraint(
            "merchant_id",
            "external_reference",
            name="uq_payment_intents_merchant_external_reference",
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
        default="requires_payment_method",
        server_default="requires_payment_method",
        nullable=False,
    )

    last_error_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
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
