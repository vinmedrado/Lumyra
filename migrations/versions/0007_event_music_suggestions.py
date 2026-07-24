"""event music suggestions

Revision ID: 0007_event_music_suggestions
Revises: 0006_event_playlist_experience
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_event_music_suggestions"
down_revision = "0006_event_playlist_experience"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _has_table("event_music_suggestions"):
        return

    op.create_table(
        "event_music_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=True),
        sa.Column("guest_name", sa.String(length=180), nullable=True),
        sa.Column("song_name", sa.String(length=180), nullable=False),
        sa.Column("artist_name", sa.String(length=180), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(length=60), nullable=False, server_default="guest_portal"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_event_music_suggestions_event", "event_music_suggestions", ["tenant_id", "event_id"])
    op.create_index("idx_music_suggestions_event_status", "event_music_suggestions", ["tenant_id", "event_id", "status"])


def downgrade() -> None:
    if _has_table("event_music_suggestions"):
        op.drop_index("idx_music_suggestions_event_status", table_name="event_music_suggestions")
        op.drop_index("idx_event_music_suggestions_event", table_name="event_music_suggestions")
        op.drop_table("event_music_suggestions")
