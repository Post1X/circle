from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_01_29_0000'
down_revision = '2025_10_04_0030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add unique constraint to username field
    op.create_unique_constraint('uq_user_username', 'user', ['username'])


def downgrade() -> None:
    # Remove unique constraint from username field
    op.drop_constraint('uq_user_username', 'user', type_='unique')
