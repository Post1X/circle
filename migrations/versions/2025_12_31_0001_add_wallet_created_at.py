from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_12_31_0001'
down_revision = '2025_12_31_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('wallet', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade() -> None:
    op.drop_column('wallet', 'created_at')


