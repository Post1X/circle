"""add skill usage table

Revision ID: 2026_01_07_0000
Revises: 2025_12_31_0001
Create Date: 2026-01-07 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2026_01_07_0000'
down_revision: Union[str, Sequence[str], None] = '2025_12_31_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'skill_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skill_type', sa.String(length=20), nullable=False),
        sa.Column('cost', sa.DECIMAL(precision=18, scale=6), nullable=False),
        sa.Column('balance_before', sa.DECIMAL(precision=18, scale=6), nullable=False),
        sa.Column('balance_after', sa.DECIMAL(precision=18, scale=6), nullable=False),
        sa.Column('is_free', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['game_session.session_id'], ondelete='CASCADE'),
    )
    op.create_index('ix_skill_usage_id', 'skill_usage', ['id'], unique=False)
    op.create_index('ix_skill_usage_user_id', 'skill_usage', ['user_id'], unique=False)
    op.create_index('ix_skill_usage_session_id', 'skill_usage', ['session_id'], unique=False)
    op.create_index('ix_skill_usage_created_at', 'skill_usage', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_skill_usage_created_at', table_name='skill_usage')
    op.drop_index('ix_skill_usage_session_id', table_name='skill_usage')
    op.drop_index('ix_skill_usage_user_id', table_name='skill_usage')
    op.drop_index('ix_skill_usage_id', table_name='skill_usage')
    op.drop_table('skill_usage')

