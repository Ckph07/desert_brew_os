"""
ProductionBatch Model - Tracks brewery production batches.

6-state lifecycle: PLANNED → BREWING → FERMENTING → CONDITIONING → PACKAGING → COMPLETED
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
import enum


class BatchStatus(str, enum.Enum):
    """
    Production batch lifecycle states.
    
    Workflow:
    1. PLANNED: Recipe selected, materials reserved (not yet allocated)
    2. BREWING: Active brewing (mash/boil), costs allocated via FIFO
    3. FERMENTING: In fermenter (primary fermentation)
    4. CONDITIONING: Cold conditioning/lagering
    5. PACKAGING: Being packaged to kegs/bottles
    6. COMPLETED: Ready for transfer to Taproom
    7. CANCELLED: Batch aborted
    """
    PLANNED = "planned"
    BREWING = "brewing"
    FERMENTING = "fermenting"
    CONDITIONING = "conditioning"
    PACKAGING = "packaging"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProductionBatch(Base):
    """
    Production batch tracking with state machine and cost allocation.
    
    Links:
    - Recipe (template)
    - BatchIngredientAllocation (FIFO costs from StockBatch)
    - FinishedProductInventory (output)
    - InternalTransfer (Factory → Taproom pricing)
    """
    __tablename__ = "production_batches"
    
    id = Column(Integer, primary_key=True)
    
    # Batch identification
    batch_number = Column(String(50), unique=True, nullable=False, index=True)  # "IPA-2026-001"
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    recipe_name = Column(String(200), nullable=False)  # Denormalized for quick access
    
    # Status tracking
    status = Column(String(20), nullable=False, default=BatchStatus.PLANNED.value, index=True)
    
    # Timestamps (state transitions)
    planned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    brewing_started_at = Column(DateTime)
    fermenting_started_at = Column(DateTime)
    conditioning_started_at = Column(DateTime)
    packaging_started_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Quantities
    planned_volume_liters = Column(Numeric(10, 2), nullable=False)
    actual_volume_liters = Column(Numeric(10, 2))  # Measured after losses
    
    # Measurements (optional for Sprint 4)
    actual_og = Column(Numeric(4, 3))  # Measured Original Gravity
    actual_fg = Column(Numeric(4, 3))  # Measured Final Gravity
    actual_abv = Column(Numeric(4, 2)) # Calculated ABV
    
    # Cost tracking (populated by CostAllocator)
    total_cost = Column(Numeric(12, 2))          # Total production cost (FIFO allocated)
    cost_per_liter = Column(Numeric(10, 2))      # = total_cost / actual_volume_liters
    
    # Cost breakdown (denormalized for reporting)
    malt_cost = Column(Numeric(10, 2))
    hops_cost = Column(Numeric(10, 2))
    yeast_cost = Column(Numeric(10, 2))
    water_cost = Column(Numeric(10, 2))
    labor_cost = Column(Numeric(10, 2))  # Fixed for Sprint 4
    overhead_cost = Column(Numeric(10, 2))  # Fixed for Sprint 4
    
    # Links to output
    finished_product_id = Column(Integer)  # FK to FinishedProductInventory (Sprint 2.5)
    internal_transfer_id = Column(UUID(as_uuid=True))  # FK to InternalTransfer (Sprint 3.5)
    
    # Metadata
    notes = Column(Text)
    created_by_user_id = Column(Integer)
    cancellation_reason = Column(String(500))
    
    def __repr__(self):
        return f"<ProductionBatch(batch_number='{self.batch_number}', status='{self.status}', volume={self.actual_volume_liters}L)>"
    
    @property
    def is_complete(self) -> bool:
        """Check if batch is completed."""
        return self.status == BatchStatus.COMPLETED.value
    
    @property
    def days_in_production(self) -> int:
        """Calculate days from start to completion."""
        if not self.brewing_started_at:
            return 0
        end_date = self.completed_at or datetime.utcnow()
        return (end_date - self.brewing_started_at).days
    
    @property
    def yield_percentage(self) -> float:
        """Calculate actual vs planned yield."""
        if not self.actual_volume_liters or not self.planned_volume_liters:
            return 0.0
        return round((float(self.actual_volume_liters) / float(self.planned_volume_liters)) * 100, 2)
