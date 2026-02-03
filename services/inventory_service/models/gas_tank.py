"""
GasTank model for tracking CO2/O2 tanks as individual assets.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class GasTank(Base):
    """
    Individual gas tank tracking (CO2, O2).
    
    Each tank is a unique asset (not fungible like raw materials).
    Tanks are usually rented with deposit and must be returned.
    """
    __tablename__ = "gas_tanks"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identity
    tank_code = Column(String(50), nullable=False, unique=True, index=True)  # "CO2-TANK-001"
    sku = Column(String(50), nullable=False, index=True)  # "CO2-FOOD-10KG", "O2-1M3"
    
    # Capacity
    capacity_kg = Column(Numeric(6, 2), nullable=True)  # For CO2: 10, 25
    capacity_m3 = Column(Numeric(6, 3), nullable=True)  # For O2: 1.0
    current_weight_kg = Column(Numeric(6, 2), nullable=True)
    current_volume_m3 = Column(Numeric(6, 3), nullable=True)
    
    # Status flags
    is_full = Column(Boolean, nullable=False, default=True)
    is_empty = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="FULL")  # FULL, IN_USE, EMPTY, MAINTENANCE
    
    # Ownership
    ownership_type = Column(String(20), nullable=False)  # RENTED, DEPOSIT
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    deposit_amount = Column(Numeric(10, 2), nullable=True)
    
    # Location
    location = Column(String(100), nullable=True)  # "Production Floor", "Storage"
    
    # Dates
    last_filled_at = Column(DateTime, nullable=True)
    last_inspected_at = Column(DateTime, nullable=True)
    next_inspection_due = Column(Date, nullable=True)
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("Supplier")
    consumptions = relationship("GasConsumption", back_populates="tank")
    
    # Indexes
    __table_args__ = (
        Index('idx_gas_status', 'status', 'sku'),
        Index('idx_gas_location', 'location', 'status'),
    )
    
    def __repr__(self):
        return (
            f"<GasTank("
            f"code='{self.tank_code}', "
            f"sku='{self.sku}', "
            f"status={self.status}"
            f")>"
        )
    
    @property
    def remaining_percentage(self) -> float:
        """Calculate remaining capacity percentage."""
        if self.capacity_kg:
            if not self.current_weight_kg or self.capacity_kg == 0:
                return 0.0
            return float((self.current_weight_kg / self.capacity_kg) * 100)
        elif self.capacity_m3:
            if not self.current_volume_m3 or self.capacity_m3 == 0:
                return 0.0
            return float((self.current_volume_m3 / self.capacity_m3) * 100)
        return 0.0


class GasConsumption(Base):
    """
    Records gas consumption events.
    """
    __tablename__ = "gas_consumption"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tank reference
    tank_id = Column(Integer, ForeignKey("gas_tanks.id"), nullable=False, index=True)
    
    # Consumption amounts
    quantity_consumed_kg = Column(Numeric(6, 2), nullable=True)
    quantity_consumed_m3 = Column(Numeric(6, 3), nullable=True)
    
    # Context
    production_batch_id = Column(Integer, nullable=True)  # If used in production
    purpose = Column(String(50), nullable=False)  # "CARBONATION", "PUSHING", "AERATION"
    notes = Column(String(500), nullable=True)
    
    # Tracking
    consumed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    recorded_by = Column(String(100), nullable=True)
    
    # Relationships
    tank = relationship("GasTank", back_populates="consumptions")
    
    def __repr__(self):
        return (
            f"<GasConsumption("
            f"tank_id={self.tank_id}, "
            f"purpose='{self.purpose}', "
            f"amount={self.quantity_consumed_kg or self.quantity_consumed_m3}"
            f")>"
        )
