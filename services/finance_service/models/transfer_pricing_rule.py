"""
Transfer Pricing Rule Model - Defines pricing strategy by origin.

Purpose: Determine how Factory prices products to Taproom based on origin type.
Enables profit center separation without fiscal invoices.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from database import Base
from datetime import datetime
import enum


class PricingStrategy(str, enum.Enum):
    """
    Pricing strategy for internal transfers.
    
    Business Rules:
    - COST_PLUS: Factory earns margin (HOUSE beer) → Transfer Price = Cost × 1.15
    - PASSTHROUGH: Factory earns 0% (GUEST/COMMERCIAL) → Transfer Price = Cost × 1.00
    - FIXED_MARKUP: Custom markup percentage
    """
    COST_PLUS = "cost_plus"          # Factory profit (HOUSE beer)
    PASSTHROUGH = "passthrough"      # No factory profit (GUEST)
    FIXED_MARKUP = "fixed_markup"    # Custom percentage


class TransferPricingRule(Base):
    """
    Transfer pricing rules by product origin.
    
    Example:
    - HOUSE beer: COST_PLUS with 15% markup → Factory earns 15%
    - GUEST beer: PASSTHROUGH with 0% markup → Factory is 3PL
    - COMMERCIAL: PASSTHROUGH with 0% markup → Factory is logistics
    """
    __tablename__ = "transfer_pricing_rules"
    
    id = Column(Integer, primary_key=True)
    
    # Rule identification
    origin_type = Column(String(20), unique=True, nullable=False, index=True)  # HOUSE, GUEST, etc.
    strategy = Column(String(20), nullable=False)  # PricingStrategy enum
    
    # Markup configuration
    markup_percentage = Column(Numeric(5, 2), nullable=False)  # 15.00 = 15%
    
    # Display
    rule_name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<TransferPricingRule(origin='{self.origin_type}', strategy='{self.strategy}', markup={self.markup_percentage}%)>"
    
    def calculate_transfer_price(self, cost: float) -> float:
        """
        Calculate transfer price from cost.
        
        Args:
            cost: Unit cost from inventory/production
            
        Returns:
            Transfer price to charge Taproom
        """
        multiplier = 1.0 + (float(self.markup_percentage) / 100.0)
        return round(cost * multiplier, 2)
    
    @property
    def effective_markup(self) -> str:
        """Formatted markup for display."""
        return f"{float(self.markup_percentage):.1f}%"
