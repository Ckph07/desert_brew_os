"""Create keg_transitions table

Revision ID: 002_create_keg_transitions
Revises: 001_create_keg_assets
Create Date: 2026-02-02 14:26:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_create_keg_transitions'
down_revision: Union[str, None] = '001_create_keg_assets'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create keg_transitions table for audit trail."""
    op.create_table(
        'keg_transitions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('keg_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_state', sa.String(20), nullable=False),
        sa.Column('to_state', sa.String(20), nullable=False),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.String(200), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('bulk_operation_id', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['keg_id'], ['keg_assets.id'], name='fk_keg'),
    )
    
    # Create indexes
    op.create_index('idx_transition_keg', 'keg_transitions', ['keg_id'])
    op.create_index('idx_transition_keg_time', 'keg_transitions', ['keg_id', 'timestamp'])
    op.create_index('idx_transition_to_state', 'keg_transitions', ['to_state'])
    op.create_index('idx_transition_bulk', 'keg_transitions', ['bulk_operation_id'])


def downgrade() -> None:
    """Drop keg_transitions table."""
    op.drop_index('idx_transition_bulk', table_name='keg_transitions')
    op.drop_index('idx_transition_to_state', table_name='keg_transitions')
    op.drop_index('idx_transition_keg_time', table_name='keg_transitions')
    op.drop_index('idx_transition_keg', table_name='keg_transitions')
    op.drop_table('keg_transitions')
