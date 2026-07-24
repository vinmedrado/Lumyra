"""invitation groups for guest portal

Revision ID: 0008_invitation_groups_guest_portal
Revises: 0007_event_music_suggestions
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_invitation_groups"
down_revision = "0007_event_music_suggestions"
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
    return column_name in [column["name"] for column in inspector.get_columns(table_name)]


def _add_column_if_missing(table_name: str, column_name: str, column_type, **kwargs) -> None:
    if not _has_table(table_name):
        return
    if _has_column(table_name, column_name):
        return
    op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))


def upgrade() -> None:
    _add_column_if_missing("guests", "invitation_type", sa.String(length=30), server_default="individual")
    _add_column_if_missing("guests", "invitation_label", sa.String(length=255))

    bind = op.get_bind()
    if _has_table("guests"):
        bind.execute(sa.text("UPDATE guests SET invitation_type = CASE WHEN COALESCE(group_name, '') <> '' THEN 'family' ELSE 'individual' END WHERE invitation_type IS NULL OR invitation_type = ''"))
        bind.execute(sa.text("UPDATE guests SET invitation_label = COALESCE(NULLIF(group_name, ''), name) WHERE invitation_label IS NULL OR invitation_label = ''"))


def downgrade() -> None:
    pass
