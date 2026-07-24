"""realtime notifications collaboration

Revision ID: 0005_realtime_notifications
Revises: 0004_backend_consolidation
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_realtime_notifications'
down_revision = '0004_backend_consolidation'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(40), nullable=False, server_default='info'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(30), nullable=False, server_default='info'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('related_entity_type', sa.String(80), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),
    )
    op.create_index('idx_notifications_tenant_read', 'notifications', ['tenant_id','is_read','created_at'])
    op.create_table('activity_feed',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(80), nullable=False),
        sa.Column('entity_type', sa.String(80), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_activity_tenant_created', 'activity_feed', ['tenant_id','created_at'])
    op.create_table('online_users',
        sa.Column('user_id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), primary_key=True, server_default='1'),
        sa.Column('last_seen', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('current_page', sa.String(255), nullable=True),
        sa.Column('is_online', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.create_table('entity_locks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('entity_type', sa.String(80), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id','entity_type','entity_id', name='uq_entity_lock'),
    )

def downgrade() -> None:
    op.drop_table('entity_locks')
    op.drop_table('online_users')
    op.drop_index('idx_activity_tenant_created', table_name='activity_feed')
    op.drop_table('activity_feed')
    op.drop_index('idx_notifications_tenant_read', table_name='notifications')
    op.drop_table('notifications')
