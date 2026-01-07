"""add game player stats table

Revision ID: 2026_01_07_0001
Revises: 2026_01_07_0000
Create Date: 2026-01-07 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2026_01_07_0001'
down_revision: Union[str, Sequence[str], None] = '2026_01_07_0000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'game_player_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('skills_used_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skills_cost_total', sa.DECIMAL(precision=18, scale=6), nullable=False, server_default='0'),
        sa.Column('final_winnings', sa.DECIMAL(precision=18, scale=6), nullable=False, server_default='0'),
        sa.Column('final_rank', sa.Integer(), nullable=True),
        sa.Column('game_duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('exit_type', sa.String(length=20), nullable=False),
        sa.Column('teleport_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shield_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('boost_uses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('free_teleport_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('bonus_zone_collected', sa.DECIMAL(precision=18, scale=6), nullable=False, server_default='0'),
        sa.Column('outside_zone_damage', sa.DECIMAL(precision=18, scale=6), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['game_session.session_id'], ondelete='CASCADE'),
    )
    op.create_index('ix_game_player_stats_id', 'game_player_stats', ['id'], unique=False)
    op.create_index('ix_game_player_stats_user_id', 'game_player_stats', ['user_id'], unique=False)
    op.create_index('ix_game_player_stats_session_id', 'game_player_stats', ['session_id'], unique=False)
    op.create_index('ix_game_player_stats_created_at', 'game_player_stats', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_game_player_stats_created_at', table_name='game_player_stats')
    op.drop_index('ix_game_player_stats_session_id', table_name='game_player_stats')
    op.drop_index('ix_game_player_stats_user_id', table_name='game_player_stats')
    op.drop_index('ix_game_player_stats_id', table_name='game_player_stats')
    op.drop_table('game_player_stats')

