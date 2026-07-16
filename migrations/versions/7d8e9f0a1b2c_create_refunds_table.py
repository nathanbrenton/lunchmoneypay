"""Create refunds table.

Revision ID: 7d8e9f0a1b2c
Revises: 669aa597de34
Create Date: 2026-07-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7d8e9f0a1b2c"
down_revision: str | Sequence[str] | None = "669aa597de34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create refunds and support refund lifecycle events."""

    op.create_table(
        "refunds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("payment_intent_id", sa.Uuid(), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            sa.String(length=40),
            server_default="succeeded",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount_minor > 0",
            name="ck_refunds_amount_positive",
        ),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_refunds_currency_format",
        ),
        sa.CheckConstraint(
            "status IN ('succeeded')",
            name="ck_refunds_status",
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
        ),
        sa.ForeignKeyConstraint(
            ["payment_intent_id"],
            ["payment_intents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "merchant_id",
            "external_reference",
            name="uq_refunds_merchant_external_reference",
        ),
    )

    op.drop_constraint(
        "ck_payment_events_event_type",
        "payment_events",
        type_="check",
    )

    op.create_check_constraint(
        "ck_payment_events_event_type",
        "payment_events",
        "event_type IN ("
        "'payment_intent.succeeded', "
        "'payment_intent.payment_failed', "
        "'payment_intent.canceled', "
        "'refund.succeeded'"
        ")",
    )


def downgrade() -> None:
    """Remove refunds and refund lifecycle-event support."""

    op.drop_constraint(
        "ck_payment_events_event_type",
        "payment_events",
        type_="check",
    )

    op.create_check_constraint(
        "ck_payment_events_event_type",
        "payment_events",
        "event_type IN ("
        "'payment_intent.succeeded', "
        "'payment_intent.payment_failed', "
        "'payment_intent.canceled'"
        ")",
    )

    op.drop_table("refunds")
