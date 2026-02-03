"""
StockMovement model - Audit trail for all inventory movements.

Provides complete traceability of stock changes.
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.sql import func
from datetime import datetime
from database import Base


class StockMovement(Base):
    """
    Audit trail for all stock movements.
    
    Every change to stock is logged here with full context:
    - What moved
    - How much
    - From where to where
    - Why
    - Who authorized it
    """
    __tablename__ = "stock_movements"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # What moved
    batch_id = Column(Integer, ForeignKey("stock_batches.id"), nullable=True, index=True)
    sku = Column(String(50), nullable=False, index=True)
    
    # Movement details
    movement_type = Column(String(20), nullable=False, index=True)  # MovementType enum
    movement_origin = Column(String(30), nullable=True)  # MovementOrigin enum
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_measure = Column(String(10), nullable=False)
    
    # Locations (for transfers)
    from_location = Column(String(100), nullable=True)
    to_location = Column(String(100), nullable=True)
    
    # Cost tracking
    unit_cost = Column(Numeric(10, 2), nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)
    
    # Traceability
    reference = Column(String(200), nullable=True)  # "Production Order #42", "Venta #123"
    notes = Column(String(500), nullable=True)
    
    # Who and when
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Related entities (optional foreign keys)
    production_order_id = Column(Integer, nullable=True)
    sales_order_id = Column(Integer, nullable=True)
    transfer_id = Column(Integer, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_movement_date_type', 'created_at', 'movement_type'),
        Index('idx_movement_sku_date', 'sku', 'created_at'),
    )
    
    def __repr__(self):
        return (
            f"<StockMovement("
            f"type={self.movement_type}, "
            f"sku='{self.sku}', "
            f"qty={self.quantity}, "
            f"ref='{self.reference}'"
            f")>"
        )
