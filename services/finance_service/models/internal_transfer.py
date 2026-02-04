"""
Internal Transfer Model - Shadow Ledger for P&L segregation.

Purpose: Record internal movements between profit centers WITHOUT fiscal invoices.
Enables Factory P&L vs Taproom P&L separation.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
import enum


class ProfitCenter(str, enum.Enum):
    """
    Profit centers in Desert Brew.
    
    Business Model:
    - FACTORY: Production facility (earns margin on HOUSE beer)
    - TAPROOM: Retail location (earns margin on all sales)
    - DISTRIBUTION: B2B sales (future)
    """
    FACTORY = "factory"
    TAPROOM = "taproom"
    DISTRIBUTION = "distribution"


class InternalTransfer(Base):
    """
    Shadow Ledger for internal transfers.
    
    Records movements from Factory → Taproom for accounting purposes
    WITHOUT generating fiscal invoices (CFDI).
    
    Example:
    - 10 kegs IPA transferred from Factory to Taproom
    - Cost: $500 (production cost)
    - Transfer Price: $575 (cost + 15%)
    - Factory Revenue: $575
    - Factory Profit: $75 (15%)
    - Taproom COGS: $575 (starting point for markup)
    """
    __tablename__ = "internal_transfers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    # Transfer parties
    from_profit_center = Column(String(20), nullable=False, index=True)  # ProfitCenter enum
    to_profit_center = Column(String(20), nullable=False, index=True)
    
    # Product reference
    product_sku = Column(String(100), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    origin_type = Column(String(20), nullable=False)  # HOUSE, GUEST, etc.
    
    # Quantities
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_measure = Column(String(20), nullable=False)  # KEGS, BOTTLES, etc.
    
    # Pricing (all in MXN)
    unit_cost = Column(Numeric(10, 2), nullable=False)           # Factory's cost
    unit_transfer_price = Column(Numeric(10, 2), nullable=False) # Price to Taproom
    
    total_cost = Column(Numeric(12, 2), nullable=False)          # qty × unit_cost
    total_transfer_price = Column(Numeric(12, 2), nullable=False) # qty × unit_transfer_price
    
    # Profit center impact
    factory_revenue = Column(Numeric(12, 2), nullable=False)     # = total_transfer_price
    factory_profit = Column(Numeric(12, 2), nullable=False)      # = total_transfer_price - total_cost
    taproom_cogs = Column(Numeric(12, 2), nullable=False)        # = total_transfer_price
    
    # Transfer pricing rule applied
    pricing_rule_id = Column(Integer, ForeignKey('transfer_pricing_rules.id'))
    markup_percentage = Column(Numeric(5, 2))  # Denormalized for audit
    
    # Timestamps
    transfer_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    notes = Column(String(500))
    created_by_user_id = Column(Integer)  # User who initiated transfer
    
    def __repr__(self):
        return f"<InternalTransfer(from={self.from_profit_center}, to={self.to_profit_center}, sku='{self.product_sku}', qty={self.quantity})>"
    
    @property
    def factory_margin_percentage(self) -> float:
        """Calculate factory profit margin %."""
        if float(self.total_cost) == 0:
            return 0.0
        return round((float(self.factory_profit) / float(self.total_cost)) * 100, 2)
