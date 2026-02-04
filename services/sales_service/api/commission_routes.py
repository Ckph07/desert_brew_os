"""
FastAPI routes for Commission Tiers.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.commission_tier import CommissionTier
from schemas.commission import CommissionTierResponse, SellerTierResponse

router = APIRouter(prefix="/api/v1/sales", tags=["Sales"])


@router.get("/commission-tiers", response_model=List[CommissionTierResponse])
def get_commission_tiers(
    active_only: bool = Query(True, description="Show only active tiers"),
    db: Session = Depends(get_db)
):
    """
    Get all commission tiers.
    
    Returns tiers ordered by min_monthly_liters descending (Platinum first).
    """
    query = db.query(CommissionTier)
    
    if active_only:
        query = query.filter_by(is_active=True)
    
    tiers = query.order_by(CommissionTier.min_monthly_liters.desc()).all()
    return tiers


@router.get("/sellers/{user_id}/tier", response_model=SellerTierResponse)
def get_seller_current_tier(user_id: int, db: Session = Depends(get_db)):
    """
    Determine seller's current tier based on monthly volume.
    
    NOTE: Actual commission calculation happens in Sprint 6 (after PoD implementation).
    For now, returns mock data.
    """
    # TODO: Replace with actual delivered orders when implemented
    # This is a placeholder for Sprint 3
    # In Sprint 6, this will query:
    # SELECT SUM(total_liters) FROM orders
    # WHERE assigned_user_id = user_id
    #   AND delivered_at >= current_month_start
    #   AND status = 'DELIVERED'
    
    # Mock volume for demonstration
    volume = 0.0  # Will be populated in Sprint 6
    
    # Find matching tier
    tier = db.query(CommissionTier).filter(
        CommissionTier.min_monthly_liters <= volume,
        CommissionTier.is_active == True
    ).order_by(CommissionTier.min_monthly_liters.desc()).first()
    
    # Find next tier
    next_tier_obj = None
    if tier:
        next_tier_obj = db.query(CommissionTier).filter(
            CommissionTier.min_monthly_liters > volume,
            CommissionTier.is_active == True
        ).order_by(CommissionTier.min_monthly_liters.asc()).first()
    
    next_tier = None
    if next_tier_obj:
        next_tier = {
            "name": next_tier_obj.name,
            "min_liters": float(next_tier_obj.min_monthly_liters),
            "rate": float(next_tier_obj.commission_rate_per_liter),
            "liters_needed": float(next_tier_obj.min_monthly_liters - volume)
        }
    
    commission_rate = float(tier.commission_rate_per_liter) if tier else 0.0
    projected_commission = volume * commission_rate
    
    return SellerTierResponse(
        user_id=user_id,
        current_month_volume_liters=volume,
        current_tier=tier.name if tier else "None",
        commission_rate=commission_rate,
        next_tier=next_tier,
        projected_monthly_commission=projected_commission
    )
