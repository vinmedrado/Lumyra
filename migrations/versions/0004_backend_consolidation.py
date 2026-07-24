"""backend consolidation: sessions, jobs, scheduler and analytics snapshots

Revision ID: 0004_backend_consolidation
Revises: 0003_saas_advanced
Create Date: 2026-05-05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_backend_consolidation"
down_revision = "0003_saas_advanced"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
    )
    op.create_index("idx_user_sessions_user_active", "user_sessions", ["user_id", "revoked_at", "expires_at"])
    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.String(length=10), nullable=False),
        sa.Column("total_guests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confirmed_guests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_guests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("declined_guests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expenses_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expenses_paid", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tables_occupancy_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "event_id", "snapshot_date", name="uq_snapshot_day"),
    )
    for table, cols in {
        "background_jobs": [
            ("max_retries", sa.Integer(), "3"),
            ("retry_count", sa.Integer(), "0"),
            ("priority", sa.Integer(), "100"),
            ("locked_by", sa.String(length=120), None),
            ("locked_at", sa.DateTime(), None),
            ("metadata_json", sa.Text(), None),
        ],
        "automation_rule_advanced": [
            ("schedule_type", sa.String(length=30), "manual"),
            ("interval_minutes", sa.Integer(), None),
            ("daily_time", sa.String(length=10), None),
            ("next_run_at", sa.DateTime(), None),
            ("last_run_at", sa.DateTime(), None),
        ],
        "automation_run_advanced": [
            ("error_message", sa.Text(), None),
            ("affected_count", sa.Integer(), "0"),
        ],
        "audit_logs": [
            ("ip", sa.String(length=80), None),
            ("user_agent", sa.String(length=512), None),
            ("request_id", sa.String(length=64), None),
            ("severity", sa.String(length=20), "info"),
        ],
    }.items():
        for name, col_type, default in cols:
            _add_column_if_missing(
                table,
                name,
                col_type,
                server_default=default,
            )


def downgrade() -> None:
    op.drop_table("analytics_snapshots")
    op.drop_index("idx_user_sessions_user_active", table_name="user_sessions")
    op.drop_table("user_sessions")

def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if table_name not in inspector.get_table_names():
        return False

    return column_name in [c["name"] for c in inspector.get_columns(table_name)]


def _add_column_if_missing(table_name, column_name, column_type, **kwargs):
    if not _has_table(table_name):
        return

    if _has_column(table_name, column_name):
        return

    op.add_column(
        table_name,
        sa.Column(column_name, column_type, **kwargs)
    )