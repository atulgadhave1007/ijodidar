"""sprint4: billing_period on membership_plans, soft-delete on messages

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'b4c5d6e7f8a9'
down_revision = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None


def upgrade():
    # billing_period on membership_plans (default 'monthly')
    op.add_column('membership_plans',
        sa.Column('billing_period', sa.String(10), nullable=False,
                  server_default='monthly'))

    # soft-delete columns on messages
    op.add_column('messages',
        sa.Column('is_deleted_by_sender', sa.Boolean(), nullable=False,
                  server_default=sa.false()))
    op.add_column('messages',
        sa.Column('is_deleted_by_receiver', sa.Boolean(), nullable=False,
                  server_default=sa.false()))

    # seed annual plans
    op.execute("""
        INSERT INTO membership_plans
            (name, price_inr, duration_days, max_interests, can_message,
             can_view_phone, can_view_full_profile, highlighted, billing_period, description)
        VALUES
            ('Silver Annual',   2999, 365, 30, FALSE, FALSE, TRUE,  FALSE, 'annual',
             'Silver plan billed annually — save 37% vs monthly'),
            ('Gold Annual',     4999, 365, 60, TRUE,  TRUE,  TRUE,  TRUE,  'annual',
             'Gold plan billed annually — save 37% vs monthly'),
            ('Platinum Annual', 7999, 365, 999, TRUE,  TRUE,  TRUE,  FALSE, 'annual',
             'Platinum plan billed annually — save 37% vs monthly')
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade():
    op.drop_column('messages', 'is_deleted_by_receiver')
    op.drop_column('messages', 'is_deleted_by_sender')
    op.drop_column('membership_plans', 'billing_period')
    op.execute("""
        DELETE FROM membership_plans
        WHERE name IN ('Silver Annual', 'Gold Annual', 'Platinum Annual')
    """)
