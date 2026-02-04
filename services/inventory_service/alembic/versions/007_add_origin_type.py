"""Add origin_type to finished_product_inventory

Revision ID: 007_add_origin_type
Revises: 006_create_product_movements
Create Date: 2026-02-03 17:45:00

Critical Migration for Sprint 3: Transfer Pricing Support
- Adds origin_type field (HOUSE/GUEST/COMMERCIAL/MERCHANDISE)
- Backfills existing products based on traceability fields
- Enables Sprint 3.5 (Financial Bridge)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_add_origin_type'
down_revision: Union[str, None] = '006_create_product_movements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add origin_type column to finished_product_inventory."""
    
    # 1. Add column (nullable initially for backfill)
    op.add_column(
        'finished_product_inventory',
        sa.Column('origin_type', sa.String(20), nullable=True)
    )
    
    # 2. Backfill existing data based on traceability
    # Logic:
    # - If production_batch_id IS NOT NULL → HOUSE
    # - If guest_brewery_id IS NOT NULL → GUEST
    # - If product_type = 'COMMERCIAL' → COMMERCIAL
    # - Else → MERCHANDISE
    op.execute("""
        UPDATE finished_product_inventory
        SET origin_type = CASE
            WHEN production_batch_id IS NOT NULL THEN 'house'
            WHEN guest_brewery_id IS NOT NULL THEN 'guest'
            WHEN product_type = 'COMMERCIAL' THEN 'commercial'
            ELSE 'merchandise'
        END;
    """)
    
    # 3. Make NOT NULL after backfill
    op.alter_column(
        'finished_product_inventory',
        'origin_type',
        nullable=False
    )
    
    # 4. Add index for filtering/grouping
    op.create_index(
        'idx_fp_origin',
        'finished_product_inventory',
        ['origin_type']
    )
    
    # 5. Add composite index for Transfer Pricing queries
    op.create_index(
        'idx_fp_origin_category',
        'finished_product_inventory',
        ['origin_type', 'category']
    )


def downgrade() -> None:
    """Remove origin_type column."""
    op.drop_index('idx_fp_origin_category', table_name='finished_product_inventory')
    op.drop_index('idx_fp_origin', table_name='finished_product_inventory')
    op.drop_column('finished_product_inventory', 'origin_type')
