"""Add failed payment-intent state for the bounded demo checkout contract.

Revision ID: a0b1c2d3e4f5
Revises: 9f0a1b2c3d4e
Create Date: 2026-07-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a0b1c2d3e4f5"
down_revision: str | Sequence[str] | None = "9f0a1b2c3d4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow an explicit terminal failed state for declined demo checkouts."""

    op.drop_constraint(
        "ck_payment_intents_status",
        "payment_intents",
        type_="check",
    )
    op.create_check_constraint(
        "ck_payment_intents_status",
        "payment_intents",
        "status IN ('requires_payment_method', 'processing', "
        "'succeeded', 'failed', 'canceled')",
    )


def downgrade() -> None:
    """Restore the pre-checkout payment-intent state set."""

    op.execute(
        "UPDATE payment_intents "
        "SET status = 'requires_payment_method' "
        "WHERE status = 'failed'"
    )
    op.drop_constraint(
        "ck_payment_intents_status",
        "payment_intents",
        type_="check",
    )
    op.create_check_constraint(
        "ck_payment_intents_status",
        "payment_intents",
        "status IN ('requires_payment_method', 'processing', 'succeeded', 'canceled')",
    )
