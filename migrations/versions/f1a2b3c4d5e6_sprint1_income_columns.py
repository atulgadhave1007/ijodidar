"""sprint1_income_columns

Adds min_income_lpa / max_income_lpa Integer columns to partner_preferences.
Resolves Conflict C8 from REDESIGN_ALIGNMENT_REPORT.md.

Revision ID: f1a2b3c4d5e6
Revises: d635e7cc9b9c
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'f1a2b3c4d5e6'
down_revision = 'd635e7cc9b9c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('partner_preferences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('min_income_lpa', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('max_income_lpa', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('partner_preferences', schema=None) as batch_op:
        batch_op.drop_column('max_income_lpa')
        batch_op.drop_column('min_income_lpa')
