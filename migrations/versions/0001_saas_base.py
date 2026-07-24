"""saas base tables

Revision ID: 0001_saas_base
Revises:
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_saas_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("tenants", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(), nullable=False), sa.Column("slug", sa.String(), nullable=False, unique=True), sa.Column("created_at", sa.String()))
    op.create_table("background_jobs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer()), sa.Column("event_id", sa.Integer()), sa.Column("type", sa.String(), nullable=False), sa.Column("status", sa.String(), nullable=False, server_default="queued"), sa.Column("progress", sa.Integer(), nullable=False, server_default="0"), sa.Column("retries", sa.Integer(), nullable=False, server_default="0"), sa.Column("metadata_json", sa.Text()), sa.Column("started_at", sa.String()), sa.Column("finished_at", sa.String()), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.String()))
    op.create_table("exports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer()), sa.Column("event_id", sa.Integer()), sa.Column("export_type", sa.String(), nullable=False), sa.Column("file_path", sa.String(), nullable=False), sa.Column("status", sa.String(), nullable=False, server_default="ready"), sa.Column("created_at", sa.String()))


def downgrade() -> None:
    op.drop_table("exports")
    op.drop_table("background_jobs")
    op.drop_table("tenants")
