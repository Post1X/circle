from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '2025_01_20_0000'
down_revision = '2025_01_29_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('withdrawal_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.DECIMAL(), nullable=False),
        sa.Column('to_address', sa.String(length=42), nullable=False),
        sa.Column('fee', sa.DECIMAL(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('transaction_hash', sa.String(length=66), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('hot_wallet',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=42), nullable=False),
        sa.Column('encrypted_private_key', sa.String(length=255), nullable=False),
        sa.Column('balance', sa.DECIMAL(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address')
    )
    
    op.create_table('cold_wallet',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=42), nullable=False),
        sa.Column('balance', sa.DECIMAL(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address')
    )
    
    op.create_index(op.f('ix_withdrawal_request_user_id'), 'withdrawal_request', ['user_id'], unique=False)
    op.create_index(op.f('ix_withdrawal_request_status'), 'withdrawal_request', ['status'], unique=False)
    op.create_index(op.f('ix_withdrawal_request_created_at'), 'withdrawal_request', ['created_at'], unique=False)
    op.create_index(op.f('ix_hot_wallet_is_active'), 'hot_wallet', ['is_active'], unique=False)
    op.create_index(op.f('ix_cold_wallet_is_active'), 'cold_wallet', ['is_active'], unique=False)
    


def downgrade() -> None:
    op.drop_index(op.f('ix_cold_wallet_is_active'), table_name='cold_wallet')
    op.drop_index(op.f('ix_hot_wallet_is_active'), table_name='hot_wallet')
    op.drop_index(op.f('ix_withdrawal_request_created_at'), table_name='withdrawal_request')
    op.drop_index(op.f('ix_withdrawal_request_status'), table_name='withdrawal_request')
    op.drop_index(op.f('ix_withdrawal_request_user_id'), table_name='withdrawal_request')
    
    op.drop_table('cold_wallet')
    op.drop_table('hot_wallet')
    op.drop_table('withdrawal_request')
