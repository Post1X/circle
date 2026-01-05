"""restore hashed_password and make wallet_address nullable

Revision ID: 2025_01_28_0000
Revises: 2ecf387d9e4c
Create Date: 2025-01-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025_01_28_0000'
down_revision = '2ecf387d9e4c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add back hashed_password field
    op.add_column('user', sa.Column('hashed_password', sa.String(length=255), nullable=False, server_default=''))
    
    # Make wallet_address nullable
    op.alter_column('user', 'wallet_address', nullable=True)


def downgrade() -> None:
    # Make wallet_address not nullable
    op.alter_column('user', 'wallet_address', nullable=False)
    
    # Remove hashed_password field
    op.drop_column('user', 'hashed_password')
