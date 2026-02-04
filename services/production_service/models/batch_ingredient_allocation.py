"""
BatchIngredientAllocation Model - FIFO cost tracking.

Links ProductionBatch to StockBatch (Sprint 1) for precise cost allocation.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from database import Base
from datetime import datetime


class BatchIngredientAllocation(Base):
    """
    FIFO allocation record linking production batch to stock batches.
    
    Purpose: Track which inventory lots were consumed for which production batch.
    Enables precise cost tracing (e.g., "Batch IPA-2026-001 used Maris Otter from LOT-123 at $15/kg")
    
    Example:
    - ProductionBatch IPA-2026-001 needs 5kg Maris Otter
    - StockBatch LOT-123 has 3kg at $15/kg (oldest)
    - StockBatch LOT-124 has 10kg at $18/kg (newer)
    - FIFO allocates:
      * 3kg from LOT-123 ($45)
      * 2kg from LOT-124 ($36)
      * Total: $81
    """
    __tablename__ = "batch_ingredient_allocations"
    
    id = Column(Integer, primary_key=True)
    
    # Links
    production_batch_id = Column(Integer, ForeignKey('production_batches.id'), nullable=False, index=True)
    stock_batch_id = Column(Integer, nullable=False, index=True)  # FK to inventory_service.stock_batches
    
    # Ingredient details
    ingredient_name = Column(String(200), nullable=False)
    ingredient_category = Column(String(50))  # MALT, HOP, YEAST, ADJUNCT
    
    # Allocation details
    quantity_consumed = Column(Numeric(10, 3), nullable=False)  # Amount taken from this stock batch
    unit_measure = Column(String(20), nullable=False)  # KG, G, L, ML
    
    # Cost (from StockBatch at time of allocation)
    unit_cost = Column(Numeric(10, 2), nullable=False)  # Cost per unit from stock batch
    total_cost = Column(Numeric(10, 2), nullable=False)  # = quantity_consumed × unit_cost
    
    # Audit
    allocated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Stock batch reference (denormalized for reporting)
    stock_batch_number = Column(String(100))  # e.g., "LOT-2024-MO-001"
    supplier_name = Column(String(200))
    
    def __repr__(self):
        return f"<BatchIngredientAllocation(batch={self.production_batch_id}, ingredient='{self.ingredient_name}', qty={self.quantity_consumed}, cost=${self.total_cost})>"
    
    @property
    def cost_per_unit(self) -> float:
        """Unit cost for display."""
        return float(self.unit_cost)
