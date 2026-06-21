"""Sprint 3: add user_devices table for FCM push tokens

Revision ID: a3b4c5d6e7f8
Revises: f1a2b3c4d5e6
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3b4c5d6e7f8'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_devices',
        sa.Column('id',          sa.Integer(),     nullable=False),
        sa.Column('user_id',     sa.Integer(),     nullable=False),
        sa.Column('fcm_token',   sa.String(300),   nullable=False),
        sa.Column('platform',    sa.String(10),    nullable=False),
        sa.Column('app_version', sa.String(20),    nullable=True),
        sa.Column('last_seen',   sa.DateTime(),    nullable=True),
        sa.Column('created_at',  sa.DateTime(),    nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fcm_token', name='uq_device_fcm_token'),
    )
    op.create_index('ix_user_devices_user_id', 'user_devices', ['user_id'])


def downgrade():
    op.drop_index('ix_user_devices_user_id', table_name='user_devices')
    op.drop_table('user_devices')
