"""
Commission Tier Model - Seller incentive structure.

Purpose: Define commission rates based on monthly sales volume.
Tiers encourage volume growth (Platinum > Gold > Silver > Bronze).
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean
from database import Base


class CommissionTier(Base):
    """
    Commission rate tiers based on monthly volume.
    
    Business Rules:
    - Commissions calculated on DELIVERED liters (PoD verified)
    - Tier determined by current month's cumulative volume
    - Rate applied RETROACTIVELY if seller moves up mid-month
    """
    __tablename__ = "commission_tiers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # "Platinum"
    min_monthly_liters = Column(Numeric(10, 2), nullable=False)
    commission_rate_per_liter = Column(Numeric(6, 2), nullable=False)  # MXN/L
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Display Properties
    description = Column(String(200))  # "Top performers >500L/month"
    badge_color = Column(String(20))   # "platinum", "gold", "silver", "bronze"
    
    def __repr__(self):
        return f"<CommissionTier(name='{self.name}', min={self.min_monthly_liters}L, rate=${self.commission_rate_per_liter}/L)>"
    
    @property
    def display_rate(self) -> str:
        """Formatted rate for UI."""
        return f"${float(self.commission_rate_per_liter):.2f}/L"
    
    def calculate_commission(self, liters: float) -> float:
        """Calculate commission for given volume."""
        return float(liters) * float(self.commission_rate_per_liter)
