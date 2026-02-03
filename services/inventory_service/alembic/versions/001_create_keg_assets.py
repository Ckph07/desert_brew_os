"""Create keg_assets table

Revision ID: 001_create_keg_assets
Revises: 
Create Date: 2026-02-02 14:25:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_create_keg_assets'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create keg_assets table with all fields."""
    op.create_table(
        'keg_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('serial_number', sa.String(50), nullable=False, unique=True),
        sa.Column('rfid_tag', sa.String(100), nullable=True, unique=True),
        sa.Column('qr_code', sa.String(100), nullable=True, unique=True),
        sa.Column('size_liters', sa.Integer(), nullable=False),
        sa.Column('material', sa.String(50), nullable=False, server_default='STAINLESS_STEEL'),
        sa.Column('keg_type', sa.String(50), nullable=False, server_default='SANKE_D'),
        sa.Column('current_state', sa.String(20), nullable=False, server_default='EMPTY'),
        sa.Column('production_batch_id', sa.Integer(), nullable=True),
        sa.Column('ownership', sa.String(20), nullable=False, server_default='OWN'),
        sa.Column('guest_brewery_id', sa.Integer(), nullable=True),
        sa.Column('cycle_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_cleaned_at', sa.DateTime(), nullable=True),
        sa.Column('last_filled_at', sa.DateTime(), nullable=True),
        sa.Column('current_location', sa.String(100), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('needs_maintenance', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_keg_serial', 'keg_assets', ['serial_number'])
    op.create_index('idx_keg_rfid', 'keg_assets', ['rfid_tag'])
    op.create_index('idx_keg_qr', 'keg_assets', ['qr_code'])
    op.create_index('idx_keg_state', 'keg_assets', ['current_state'])
    op.create_index('idx_keg_state_location', 'keg_assets', ['current_state', 'current_location'])
    op.create_index('idx_keg_batch', 'keg_assets', ['production_batch_id'])
    op.create_index('idx_keg_client', 'keg_assets', ['client_id'])


def downgrade() -> None:
    """Drop keg_assets table."""
    op.drop_index('idx_keg_client', table_name='keg_assets')
    op.drop_index('idx_keg_batch', table_name='keg_assets')
    op.drop_index('idx_keg_state_location', table_name='keg_assets')
    op.drop_index('idx_keg_state', table_name='keg_assets')
    op.drop_index('idx_keg_qr', table_name='keg_assets')
    op.drop_index('idx_keg_rfid', table_name='keg_assets')
    op.drop_index('idx_keg_serial', table_name='keg_assets')
    op.drop_table('keg_assets')
