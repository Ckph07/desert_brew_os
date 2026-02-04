"""
Pydantic schemas for Commission Tiers.
"""
from pydantic import BaseModel, Field
from typing import Optional


class CommissionTierResponse(BaseModel):
    """Commission tier details."""
    id: int
    name: str
    min_monthly_liters: float
    commission_rate_per_liter: float
    description: Optional[str]
    badge_color: Optional[str]
    is_active: bool
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Platinum",
                "min_monthly_liters": 500.0,
                "commission_rate_per_liter": 2.50,
                "description": "Elite sellers >500L/month",
                "badge_color": "platinum",
                "is_active": True
            }
        }


class SellerTierResponse(BaseModel):
    """Seller's current tier status."""
    user_id: int
    current_month_volume_liters: float
    current_tier: Optional[str]
    commission_rate: float
    next_tier: Optional[dict] = None
    projected_monthly_commission: float
