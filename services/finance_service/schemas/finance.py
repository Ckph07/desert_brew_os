"""
Pydantic schemas for Transfer Pricing.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class TransferPricingRuleResponse(BaseModel):
    """Transfer pricing rule details."""
    id: int
    origin_type: str
    strategy: str
    markup_percentage: float
    rule_name: str
    description: Optional[str]
    is_active: bool
    
    class Config:
        orm_mode = True


class InternalTransferRequest(BaseModel):
    """Request to create internal transfer."""
    from_profit_center: str = Field(..., description="Source profit center (factory/taproom)")
    to_profit_center: str = Field(..., description="Destination profit center")
    product_sku: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=200)
    origin_type: str = Field(..., description="Product origin (house/guest/commercial/merchandise)")
    quantity: float = Field(..., gt=0, description="Quantity to transfer")
    unit_measure: str = Field(..., description="KEGS, BOTTLES, CANS, UNITS")
    unit_cost: float = Field(..., gt=0, description="Factory unit cost")
    notes: Optional[str] = Field(None, max_length=500)
    created_by_user_id: Optional[int] = None
    
    @validator('from_profit_center', 'to_profit_center')
    def validate_profit_center(cls, v):
        valid = ['factory', 'taproom', 'distribution']
        if v.lower() not in valid:
            raise ValueError(f"Profit center must be one of: {valid}")
        return v.lower()
    
    @validator('origin_type')
    def validate_origin(cls, v):
        valid = ['house', 'guest', 'commercial', 'merchandise']
        if v.lower() not in valid:
            raise ValueError(f"Origin type must be one of: {valid}")
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "from_profit_center": "factory",
                "to_profit_center": "taproom",
                "product_sku": "BEER-IPA-KEG-001",
                "product_name": "IPA House Keg 50L",
                "origin_type": "house",
                "quantity": 10.0,
                "unit_measure": "KEGS",
                "unit_cost": 500.00,
                "notes": "Weekly stock transfer"
            }
        }


class InternalTransferResponse(BaseModel):
    """Response after creating internal transfer."""
    id: str
    from_profit_center: str
    to_profit_center: str
    product_sku: str
    quantity: float
    unit_cost: float
    unit_transfer_price: float
    total_cost: float
    total_transfer_price: float
    factory_revenue: float
    factory_profit: float
    taproom_cogs: float
    markup_percentage: float
    transfer_date: datetime
    
    class Config:
        orm_mode = True


class ProfitCenterSummary(BaseModel):
    """P&L summary for a profit center."""
    profit_center: str
    period_start: datetime
    period_end: datetime
    
    # Revenue
    total_revenue: float
    
    # Costs
    total_cogs: float
    total_profit: float
    profit_margin_percentage: float
    
    # Metrics
    transfer_count: int
    total_liters: Optional[float] = None


class TransferPriceCalculation(BaseModel):
    """Response for transfer price calculation."""
    origin_type: str
    unit_cost: float
    unit_transfer_price: float
    markup_percentage: float
    strategy: str
    rule_name: str
