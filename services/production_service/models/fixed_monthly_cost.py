"""
FixedMonthlyCost and ProductionTarget models.

Purpose: Track monthly fixed overhead costs and production volume target
to calculate the real per-liter overhead cost.

Business Context (user's real data):
    Gasolina           $2,000
    Energía            $8,000
    Agua               $2,500
    Recursos Humanos   $25,000
    Operación Planta   $9,500
    Gas y CO₂          $7,500
    Comunicaciones     $900
    Desgaste Vehicular $2,500
    ──────────────────────────
    TOTAL              $57,900 / 1,800L = $32.17/L
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Index
from database import Base
from datetime import datetime


class FixedMonthlyCost(Base):
    """
    Monthly fixed cost line items.

    Sum of all active items = total monthly fixed costs.
    Divided by ProductionTarget.target_liters = fixed cost per liter.
    """
    __tablename__ = "fixed_monthly_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Category (for grouping/reporting)
    category = Column(String(50), nullable=False, index=True)
    # FUEL, ENERGY, WATER, HR, OPERATIONS, GAS_CO2, COMMS, VEHICLE, OTHER

    concept = Column(String(200), nullable=False)
    # Human-readable: "Gasolina", "Energía Eléctrica", etc.

    monthly_amount = Column(Numeric(12, 2), nullable=False)
    # Amount in MXN per month

    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FixedMonthlyCost(concept='{self.concept}', amount=${self.monthly_amount})>"


class ProductionTarget(Base):
    """
    Monthly production volume target.

    Used to calculate: fixed_cost_per_liter = sum(fixed_costs) / target_liters
    Only ONE active target at a time (is_current=True).
    """
    __tablename__ = "production_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)

    period = Column(String(10), nullable=False, index=True)
    # e.g. "2026-02" or "DEFAULT"

    target_liters_monthly = Column(Numeric(10, 2), nullable=False)
    # e.g. 1800

    # Auto-calculated
    total_fixed_cost = Column(Numeric(12, 2), nullable=True)
    fixed_cost_per_liter = Column(Numeric(10, 2), nullable=True)
    # = total_fixed_cost / target_liters_monthly

    is_current = Column(Boolean, nullable=False, default=False)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ProductionTarget(period='{self.period}', target={self.target_liters_monthly}L, cost/L=${self.fixed_cost_per_liter})>"
