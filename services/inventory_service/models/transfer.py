"""
StockTransfer model - For tracking transfers between locations.
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Index
from sqlalchemy.sql import func
from datetime import datetime
from database import Base


class StockTransfer(Base):
    """
    Tracks stock transfers between locations.
    
    Example: Moving 50kg of MALT-PALE-2ROW from "Silo A" to "Silo B"
    """
    __tablename__ = "stock_transfers"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # What's being transferred
    sku = Column(String(50), nullable=False, index=True)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_measure = Column(String(10), nullable=False)
    
    # Locations
    from_location = Column(String(100), nullable=False)
    to_location = Column(String(100), nullable=False)
    
    # Status tracking
    status = Column(String(20), nullable=False, default="PENDING")  # TransferStatus enum
    
    # Timestamps
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Who authorized/executed
    requested_by = Column(String(100), nullable=True)
    executed_by = Column(String(100), nullable=True)
    
    # Notes
    notes = Column(String(500), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_transfer_status', 'status', 'requested_at'),
        Index('idx_transfer_sku', 'sku', 'from_location'),
    )
    
    def __repr__(self):
        return (
            f"<StockTransfer("
            f"sku='{self.sku}', "
            f"qty={self.quantity}, "
            f"from='{self.from_location}' to='{self.to_location}', "
            f"status={self.status}"
            f")>"
        )
