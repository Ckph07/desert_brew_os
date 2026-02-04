"""
Finished Product Inventory Model - Cold Room Tracking.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
from decimal import Decimal


class FinishedProductInventory(Base):
    """
    Inventario de producto terminado en cuartos fríos.
    
    Tracks:
    - Cerveza propia (own production)
    - Cerveza comercial (Corona, Modelo, etc.)
    - Cerveza guest craft (colaboraciones)
    - Agua embotellada
    - Merchandise
    
    Unlike raw materials (FIFO), finished products track:
    - Specific locations (shelf positions)
    - Best before dates
    - Individual product runs
    """
    __tablename__ = "finished_product_inventory"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Product identification
    sku = Column(String(100), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    
    # Product classification
    product_type = Column(String(20), nullable=False, index=True)  # ProductType enum
    category = Column(String(30), nullable=False, index=True)      # ProductCategory enum
    
    # Origin (WHO produces - critical for Transfer Pricing)
    origin_type = Column(String(20), nullable=False, index=True)   # OriginType enum
    
    # Trazabilidad (depending on type)
    production_batch_id = Column(Integer, nullable=True)           # Para cerveza propia
    supplier_id = Column(Integer, nullable=True)                   # Para comercial/guest
    guest_brewery_id = Column(Integer, nullable=True)              # Para guest craft
    keg_asset_id = Column(UUID(as_uuid=True), nullable=True)       # Link to KegAsset if BEER_KEG
    
    # Quantity tracking
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_measure = Column(String(20), nullable=False)  # "BOTTLES", "KEGS", "CANS", "UNITS"
    
    # Location tracking
    cold_room_id = Column(String(50), nullable=False, index=True)  # ColdRoomLocation enum
    shelf_position = Column(String(10), nullable=True)             # "A3", "B12", etc.
    
    # Cost tracking
    unit_cost = Column(Numeric(10, 2), nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)
    
    # Date tracking
    received_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    production_date = Column(DateTime, nullable=True)              # For own production
    best_before = Column(DateTime, nullable=True)
    
    # Availability
    availability_status = Column(String(20), nullable=False, default="AVAILABLE")  # AvailabilityStatus enum
    
    # Additional metadata
    notes = Column(String(500), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_fp_type_category', 'product_type', 'category'),
        Index('idx_fp_cold_room_status', 'cold_room_id', 'availability_status'),
        Index('idx_fp_best_before', 'best_before'),
    )
    
    def __repr__(self):
        return f"<FinishedProduct(id={self.id}, sku='{self.sku}', qty={self.quantity} {self.unit_measure})>"
    
    @property
    def is_available(self) -> bool:
        """Check if product is available for sale."""
        return self.availability_status == "AVAILABLE" and self.quantity > 0
    
    def is_expiring_soon(self, days: int = 7) -> bool:
        """Check if product is expiring within X days."""
        if not self.best_before:
            return False
        
        from datetime import timedelta
        threshold = datetime.utcnow() + timedelta(days=days)
        return self.best_before <= threshold
    
    @property
    def value(self) -> Decimal:
        """Calculate current inventory value."""
        if self.unit_cost:
            return Decimal(self.quantity) * self.unit_cost
        return Decimal('0.00')
    
    def update_quantity(self, delta: Decimal) -> None:
        """
        Update quantity (positive or negative delta).
        
        Args:
            delta: Change in quantity (can be negative for deductions)
        """
        new_quantity = Decimal(self.quantity) + delta
        
        if new_quantity < 0:
            raise ValueError(f"Cannot reduce quantity below 0 (current: {self.quantity}, delta: {delta})")
        
        self.quantity = new_quantity
        self.total_cost = self.quantity * (self.unit_cost or Decimal('0.00'))
        self.updated_at = datetime.utcnow()
