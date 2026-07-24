"""advanced saas platform tables

Revision ID: 0003_saas_advanced
Revises: 0002_add_tenant_auth_columns
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_saas_advanced"
down_revision = "0002_add_tenant_auth_columns"
branch_labels = None
depends_on = None


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


def _create_table_if_missing(table_name: str, *columns) -> None:
    if _has_table(table_name):
        return

    op.create_table(table_name, *columns)


def _add_column_if_missing(table_name: str, column_name: str, column_type, **kwargs) -> None:
    if not _has_table(table_name):
        return

    if _has_column(table_name, column_name):
        return

    op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))


def upgrade() -> None:
    _create_table_if_missing(
        "api_refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer()),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.String(length=64)),
        sa.Column("revoked_at", sa.String(length=64)),
        sa.Column("created_at", sa.String(length=64)),
    )

    _create_table_if_missing(
        "automation_rule_advanced",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer()),
        sa.Column("trigger_type", sa.String(length=100), nullable=False),
        sa.Column("condition_json", sa.Text()),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("action_json", sa.Text()),
        sa.Column("is_active", sa.Integer(), server_default="1"),
        sa.Column("last_run_at", sa.String(length=64)),
        sa.Column("created_at", sa.String(length=64)),
        sa.Column("updated_at", sa.String(length=64)),
    )

    _create_table_if_missing(
        "automation_run_advanced",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="success"),
        sa.Column("executed_at", sa.String(length=64)),
        sa.Column("result_json", sa.Text()),
    )

    _create_table_if_missing(
        "onboarding_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("current_step", sa.Integer(), server_default="1"),
        sa.Column("tenant_created", sa.Integer(), server_default="0"),
        sa.Column("event_created", sa.Integer(), server_default="0"),
        sa.Column("guests_imported", sa.Integer(), server_default="0"),
        sa.Column("form_created", sa.Integer(), server_default="0"),
        sa.Column("first_campaign_sent", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.String(length=64)),
    )

    _create_table_if_missing(
        "scheduled_campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer()),
        sa.Column("scheduled_at", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="scheduled"),
        sa.Column("created_at", sa.String(length=64)),
    )

    for col, typ in [
        ("ip", sa.String(length=64)),
        ("user_agent", sa.String(length=512)),
        ("request_id", sa.String(length=128)),
        ("severity", sa.String(length=50)),
    ]:
        _add_column_if_missing("audit_logs", col, typ)


def downgrade() -> None:
    for table in [
        "scheduled_campaigns",
        "onboarding_progress",
        "automation_run_advanced",
        "automation_rule_advanced",
        "api_refresh_tokens",
    ]:
        if _has_table(table):
            op.drop_table(table)