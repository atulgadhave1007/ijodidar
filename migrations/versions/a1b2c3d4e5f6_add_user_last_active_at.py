"""Add User.last_active_at column

Revision ID: a1b2c3d4e5f6
Revises: 27c944af2966
Create Date: 2026-06-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '27c944af2966'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_active_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_users_last_active_at', ['last_active_at'], unique=False)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_last_active_at')
        batch_op.drop_column('last_active_at')
