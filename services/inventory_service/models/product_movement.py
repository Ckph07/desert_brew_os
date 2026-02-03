"""
Product Movement Tracking for Finished Products.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index
from database import Base
from datetime import datetime
from decimal import Decimal


class ProductMovement(Base):
    """
    Movement log for finished products.
    
    Tracks all changes to finished product inventory:
    - Production (ingress from brewing)
    - Sales (egress to customers)
    - Transfers (between cold rooms)
    - Adjustments (physical count corrections)
    - Damage/Expiration (write-offs)
    
    Provides complete audit trail similar to StockMovement for raw materials.
    """
    __tablename__ = "product_movements"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to finished product
    finished_product_id = Column(
        Integer,
        ForeignKey('finished_product_inventory.id'),
        nullable=False,
        index=True
    )
    
    # Movement details
    movement_type = Column(String(20), nullable=False, index=True)  # MovementType enum
    quantity = Column(Numeric(10, 2), nullable=False)
    
    # Location tracking
    from_location = Column(String(50), nullable=True)  # Source location
    to_location = Column(String(50), nullable=True)    # Destination location
    
    # Context (depending on movement type)
    sales_order_id = Column(Integer, nullable=True)    # For SALE movements
    purchase_order_id = Column(Integer, nullable=True) # For PURCHASE movements
    user_id = Column(Integer, nullable=True)           # User who performed movement
    
    # Additional info
    notes = Column(String(500), nullable=True)
    reference_number = Column(String(50), nullable=True)  # Invoice, PO, etc.
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_pm_product_time', 'finished_product_id', 'timestamp'),
        Index('idx_pm_type_time', 'movement_type', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ProductMovement(id={self.id}, type='{self.movement_type}', qty={self.quantity})>"
    
    @property
    def is_ingress(self) -> bool:
        """Check if movement increases inventory."""
        return self.movement_type in ['PRODUCTION', 'PURCHASE', 'RETURN']
    
    @property
    def is_egress(self) -> bool:
        """Check if movement decreases inventory."""
        return self.movement_type in ['SALE', 'DAMAGE', 'EXPIRATION']
    
    @classmethod
    def create_from_production(
        cls,
        finished_product_id: int,
        quantity: Decimal,
        production_batch_id: int,
        user_id: int = None
    ) -> 'ProductMovement':
        """
        Create a PRODUCTION movement.
        
        Called when packaging a production batch.
        """
        return cls(
            finished_product_id=finished_product_id,
            movement_type='PRODUCTION',
            quantity=quantity,
            to_location='COLD_ROOM_A',  # Default location
            notes=f"Production from batch {production_batch_id}",
            user_id=user_id
        )
    
    @classmethod
    def create_from_sale(
        cls,
        finished_product_id: int,
        quantity: Decimal,
        sales_order_id: int,
        from_location: str,
        user_id: int = None
    ) -> 'ProductMovement':
        """
        Create a SALE movement.
        
        Called when product is sold to customer.
        """
        return cls(
            finished_product_id=finished_product_id,
            movement_type='SALE',
            quantity=quantity,
            from_location=from_location,
            sales_order_id=sales_order_id,
            user_id=user_id
        )
