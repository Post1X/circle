"""remove unused wallet columns

Revision ID: 2025_10_04_0030
Revises: 2025_01_28_0000
Create Date: 2025-10-04 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025_10_04_0030'
down_revision = '2025_01_28_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove unused wallet columns that are not in the SQLAlchemy model
    op.drop_column('user', 'wallets')
    op.drop_column('user', 'primary_wallet_id')


def downgrade() -> None:
    # Add back the columns if needed to rollback
    op.add_column('user', sa.Column('wallets', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('user', sa.Column('primary_wallet_id', sa.String(length=50), nullable=True))
