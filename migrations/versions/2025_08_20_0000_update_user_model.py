"""update user model

Revision ID: 2025_08_20_0000
Revises: 2025_08_19_0000
Create Date: 2025-08-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_08_20_0000'
down_revision = '2025_08_19_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('user', 'username')
    op.drop_column('user', 'email')
    op.drop_column('user', 'hashed_password')
    op.alter_column('user', 'wallet_address', nullable=False)
    op.alter_column('user', 'balance', nullable=False)
    op.alter_column('user', 'total_winnings', nullable=False)


def downgrade() -> None:
    op.add_column('user', sa.Column('username', sa.String(length=255), nullable=False))
    op.add_column('user', sa.Column('email', sa.String(length=255), nullable=False))
    op.add_column('user', sa.Column('hashed_password', sa.String(length=255), nullable=False))
    op.alter_column('user', 'wallet_address', nullable=True)
    op.alter_column('user', 'balance', nullable=True)
    op.alter_column('user', 'total_winnings', nullable=True)
