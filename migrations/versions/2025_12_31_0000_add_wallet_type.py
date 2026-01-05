from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_12_31_0000'
down_revision = '2025_01_20_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('wallet', sa.Column('wallet_type', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('wallet', 'wallet_type')

