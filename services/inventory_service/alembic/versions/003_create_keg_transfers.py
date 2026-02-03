"""Create keg_transfers table

Revision ID: 003_create_keg_transfers
Revises: 002_create_keg_transitions
Create Date: 2026-02-02 14:27:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_create_keg_transfers'
down_revision: Union[str, None] = '002_create_keg_transitions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create keg_transfers table for content transfers."""
    op.create_table(
        'keg_transfers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source_keg_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_batch_id', sa.Integer(), nullable=True),
        sa.Column('target_keg_ids', postgresql.JSONB(), nullable=False),
        sa.Column('volume_transferred_liters', sa.Numeric(6, 2), nullable=False),
        sa.Column('transferred_by', sa.Integer(), nullable=True),
        sa.Column('transferred_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['source_keg_id'], ['keg_assets.id'], name='fk_source_keg'),
    )
    
    # Create indexes
    op.create_index('idx_transfer_source', 'keg_transfers', ['source_keg_id'])
    op.create_index('idx_transfer_batch', 'keg_transfers', ['source_batch_id'])


def downgrade() -> None:
    """Drop keg_transfers table."""
    op.drop_index('idx_transfer_batch', table_name='keg_transfers')
    op.drop_index('idx_transfer_source', table_name='keg_transfers')
    op.drop_table('keg_transfers')
