"""Create webhook endpoint and delivery tables.

Revision ID: 8e9f0a1b2c3d
Revises: 7d8e9f0a1b2c
Create Date: 2026-07-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8e9f0a1b2c3d"
down_revision: str | Sequence[str] | None = "7d8e9f0a1b2c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create webhook registration and delivery-attempt tables."""

    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("signing_secret", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_webhook_endpoints_status",
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "merchant_id",
            "url",
            name="uq_webhook_endpoints_merchant_url",
        ),
    )

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("webhook_endpoint_id", sa.Uuid(), nullable=False),
        sa.Column("payment_event_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('succeeded', 'failed')",
            name="ck_webhook_deliveries_status",
        ),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["payment_event_id"], ["payment_events.id"]),
        sa.ForeignKeyConstraint(
            ["webhook_endpoint_id"],
            ["webhook_endpoints.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Remove webhook delivery and endpoint tables."""

    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")
