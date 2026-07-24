"""event playlist experience

Revision ID: 0006_event_playlist_experience
Revises: 0005_realtime_notifications
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_event_playlist_experience"
down_revision = "0005_realtime_notifications"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _has_table("event_playlists"):
        return
    op.create_table(
        "event_playlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="spotify"),
        sa.Column("playlist_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="Playlist do casamento"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("etiquette_message", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "event_id", name="uq_event_playlist"),
    )
    op.create_index("idx_event_playlists_tenant_event", "event_playlists", ["tenant_id", "event_id"])


def downgrade() -> None:
    if _has_table("event_playlists"):
        op.drop_index("idx_event_playlists_tenant_event", table_name="event_playlists")
        op.drop_table("event_playlists")
