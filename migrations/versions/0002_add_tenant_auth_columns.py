"""add tenant and auth columns

Revision ID: 0002_add_tenant_auth_columns
Revises: 0001_saas_base
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_tenant_auth_columns"
down_revision = "0001_saas_base"
branch_labels = None
depends_on = None

TABLES = [
    "users",
    "events",
    "guests",
    "event_forms",
    "event_documents",
    "vendors",
    "expenses",
    "messages",
    "message_templates",
]


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if table_name not in inspector.get_table_names():
        return False

    return column_name in [col["name"] for col in inspector.get_columns(table_name)]


def _add_column_if_missing(
    table_name: str,
    column_name: str,
    column_type: sa.types.TypeEngine,
    **kwargs,
) -> None:
    if not _has_table(table_name):
        return

    if _has_column(table_name, column_name):
        return

    op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))


def upgrade() -> None:
    for table in TABLES:
        _add_column_if_missing(table, "tenant_id", sa.Integer())

    _add_column_if_missing("users", "password_hash", sa.String(length=255))
    _add_column_if_missing("users", "is_active", sa.Integer(), server_default="1")

    _add_column_if_missing("audit_logs", "tenant_id", sa.Integer())
    _add_column_if_missing("audit_logs", "user_id", sa.Integer())
    _add_column_if_missing("audit_logs", "metadata_json", sa.Text())


def downgrade() -> None:
    pass