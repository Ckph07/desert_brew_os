"""Create product_movements table

Revision ID: 006_create_product_movements
Revises: 005_create_cold_room_readings
Create Date: 2026-02-02 23:02:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_create_product_movements'
down_revision: Union[str, None] = '005_create_cold_room_readings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create product_movements table for finished product audit trail."""
    op.create_table(
        'product_movements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('finished_product_id', sa.Integer(), nullable=False),
        sa.Column('movement_type', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('from_location', sa.String(50), nullable=True),
        sa.Column('to_location', sa.String(50), nullable=True),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('reference_number', sa.String(50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['finished_product_id'], ['finished_product_inventory.id'], name='fk_finished_product'),
    )
    
    # Create indexes
    op.create_index('idx_pm_product', 'product_movements', ['finished_product_id'])
    op.create_index('idx_pm_product_time', 'product_movements', ['finished_product_id', 'timestamp'])
    op.create_index('idx_pm_type', 'product_movements', ['movement_type'])
    op.create_index('idx_pm_type_time', 'product_movements', ['movement_type', 'timestamp'])


def downgrade() -> None:
    """Drop product_movements table."""
    op.drop_index('idx_pm_type_time', table_name='product_movements')
    op.drop_index('idx_pm_type', table_name='product_movements')
    op.drop_index('idx_pm_product_time', table_name='product_movements')
    op.drop_index('idx_pm_product', table_name='product_movements')
    op.drop_table('product_movements')
