"""Create finished_product_inventory table

Revision ID: 004_create_finished_products
Revises: 003_create_keg_transfers
Create Date: 2026-02-02 23:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_create_finished_products'
down_revision: Union[str, None] = '003_create_keg_transfers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create finished_product_inventory table."""
    op.create_table(
        'finished_product_inventory',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        
        # Product identification
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('product_name', sa.String(200), nullable=False),
        
        # Product classification
        sa.Column('product_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(30), nullable=False),
        
        # Trazabilidad
        sa.Column('production_batch_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('guest_brewery_id', sa.Integer(), nullable=True),
        sa.Column('keg_asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Quantity
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit_measure', sa.String(20), nullable=False),
        
        # Location
        sa.Column('cold_room_id', sa.String(50), nullable=False),
        sa.Column('shelf_position', sa.String(10), nullable=True),
        
        # Cost
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('total_cost', sa.Numeric(12, 2), nullable=True),
        
        # Dates
        sa.Column('received_date', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('production_date', sa.DateTime(), nullable=True),
        sa.Column('best_before', sa.DateTime(), nullable=True),
        
        # Availability
        sa.Column('availability_status', sa.String(20), nullable=False, server_default='AVAILABLE'),
        
        # Additional
        sa.Column('notes', sa.String(500), nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['keg_asset_id'], ['keg_assets.id'], name='fk_keg_asset'),
    )
    
    # Create indexes
    op.create_index('idx_fp_sku', 'finished_product_inventory', ['sku'])
    op.create_index('idx_fp_type', 'finished_product_inventory', ['product_type'])
    op.create_index('idx_fp_category', 'finished_product_inventory', ['category'])
    op.create_index('idx_fp_type_category', 'finished_product_inventory', ['product_type', 'category'])
    op.create_index('idx_fp_cold_room', 'finished_product_inventory', ['cold_room_id'])
    op.create_index('idx_fp_cold_room_status', 'finished_product_inventory', ['cold_room_id', 'availability_status'])
    op.create_index('idx_fp_best_before', 'finished_product_inventory', ['best_before'])
    op.create_index('idx_fp_batch', 'finished_product_inventory', ['production_batch_id'])


def downgrade() -> None:
    """Drop finished_product_inventory table."""
    op.drop_index('idx_fp_batch', table_name='finished_product_inventory')
    op.drop_index('idx_fp_best_before', table_name='finished_product_inventory')
    op.drop_index('idx_fp_cold_room_status', table_name='finished_product_inventory')
    op.drop_index('idx_fp_cold_room', table_name='finished_product_inventory')
    op.drop_index('idx_fp_type_category', table_name='finished_product_inventory')
    op.drop_index('idx_fp_category', table_name='finished_product_inventory')
    op.drop_index('idx_fp_type', table_name='finished_product_inventory')
    op.drop_index('idx_fp_sku', table_name='finished_product_inventory')
    op.drop_table('finished_product_inventory')
