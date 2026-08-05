"""Convert remaining Float monetary fields to Numeric.

Revision ID: 0006_float_to_numeric_monetary
Revises: 0005_scheduled_tier_change
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_float_to_numeric_monetary"
down_revision = "0005_scheduled_tier_change"
branch_labels = None
depends_on = None


def _float_to_numeric(table, column, numeric_type, batch=True):
    """Safely convert a Float column to Numeric using batch mode for SQLite compat."""
    with op.batch_alter_table(table) as batch_op:
        batch_op.alter_column(
            column,
            type_=numeric_type,
            existing_type=sa.Float(),
        )


def upgrade() -> None:
    # Transaction.amount: Float -> Numeric(10,2)
    _float_to_numeric("transactions", "amount", sa.Numeric(10, 2))

    # TokenPackage.price_dt: Float -> Numeric(10,2)
    _float_to_numeric("token_packages", "price_dt", sa.Numeric(10, 2))

    # Course.price_dt: Float -> Numeric(10,2)
    _float_to_numeric("courses", "price_dt", sa.Numeric(10, 2))

    # Plan.price: Float -> Numeric(10,2)
    _float_to_numeric("plans", "price", sa.Numeric(10, 2))

    # AIUsageLog.cost_usd: Float -> Numeric(10,4)
    _float_to_numeric("ai_usage_logs", "cost_usd", sa.Numeric(10, 4))


def downgrade() -> None:
    with op.batch_alter_table("ai_usage_logs") as batch_op:
        batch_op.alter_column("cost_usd", type_=sa.Float(), existing_type=sa.Numeric(10, 4))

    with op.batch_alter_table("plans") as batch_op:
        batch_op.alter_column("price", type_=sa.Float(), existing_type=sa.Numeric(10, 2))

    with op.batch_alter_table("courses") as batch_op:
        batch_op.alter_column("price_dt", type_=sa.Float(), existing_type=sa.Numeric(10, 2))

    with op.batch_alter_table("token_packages") as batch_op:
        batch_op.alter_column("price_dt", type_=sa.Float(), existing_type=sa.Numeric(10, 2))

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column("amount", type_=sa.Float(), existing_type=sa.Numeric(10, 2))
