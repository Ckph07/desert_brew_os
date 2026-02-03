"""Create cold_room_readings table

Revision ID: 005_create_cold_room_readings
Revises: 004_create_finished_products
Create Date: 2026-02-02 23:01:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_create_cold_room_readings'
down_revision: Union[str, None] = '004_create_finished_products'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cold_room_readings table for temperature monitoring."""
    op.create_table(
        'cold_room_readings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('cold_room_id', sa.String(50), nullable=False),
        sa.Column('temperature_celsius', sa.Numeric(5, 2), nullable=False),
        sa.Column('humidity_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('alert_triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('alert_reason', sa.String(200), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_cr_room', 'cold_room_readings', ['cold_room_id'])
    op.create_index('idx_cr_room_time', 'cold_room_readings', ['cold_room_id', 'timestamp'])
    op.create_index('idx_cr_alerts', 'cold_room_readings', ['alert_triggered', 'timestamp'])


def downgrade() -> None:
    """Drop cold_room_readings table."""
    op.drop_index('idx_cr_alerts', table_name='cold_room_readings')
    op.drop_index('idx_cr_room_time', table_name='cold_room_readings')
    op.drop_index('idx_cr_room', table_name='cold_room_readings')
    op.drop_table('cold_room_readings')
