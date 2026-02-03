"""
Pydantic schemas for gas tank management.
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime, date
from typing import Optional


class GasTankCreate(BaseModel):
    """Schema for registering a new gas tank."""
    
    tank_code: str = Field(..., min_length=1, max_length=50, description="Tank physical ID")
    sku: str = Field(..., description="CO2-FOOD-10KG, CO2-FOOD-25KG, O2-1M3")
    
    capacity_kg: Optional[Decimal] = Field(None, gt=0, description="Capacity in kg (for CO2)")
    capacity_m3: Optional[Decimal] = Field(None, gt=0, description="Capacity in m³ (for O2)")
    
    ownership_type: str = Field(..., description="RENTED or DEPOSIT")
    supplier_id: int
    deposit_amount: Optional[Decimal] = Field(None, ge=0)
    location: str = Field(..., max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tank_code": "CO2-TANK-001",
                "sku": "CO2-FOOD-25KG",
                "capacity_kg": 25.0,
                "ownership_type": "RENTED",
                "supplier_id": 1,
                "deposit_amount": 500.00,
                "location": "Production Floor"
            }
        }


class GasTankResponse(BaseModel):
    """Schema for gas tank response."""
    
    id: int
    tank_code: str
    sku: str
    
    capacity_kg: Optional[Decimal]
    capacity_m3: Optional[Decimal]
    current_weight_kg: Optional[Decimal]
    current_volume_m3: Optional[Decimal]
    
    is_full: bool
    is_empty: bool
    status: str
    remaining_percentage: float
    
    ownership_type: str
    supplier_id: Optional[int]
    deposit_amount: Optional[Decimal]
    location: Optional[str]
    
    last_filled_at: Optional[datetime]
    next_inspection_due: Optional[date]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class GasConsumptionCreate(BaseModel):
    """Schema for recording gas consumption."""
    
    tank_code: str = Field(..., description="Tank code")
    quantity_kg: Optional[Decimal] = Field(None, gt=0, description="Amount consumed in kg")
    quantity_m3: Optional[Decimal] = Field(None, gt=0, description="Amount consumed in m³")
    
    production_batch_id: Optional[int] = None
    purpose: str = Field(..., description="CARBONATION, PUSHING, AERATION")
    notes: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tank_code": "CO2-TANK-001",
                "quantity_kg": 5.0,
                "production_batch_id": 42,
                "purpose": "CARBONATION",
                "notes": "Carbonating IPA batch #42"
            }
        }


class GasConsumptionResponse(BaseModel):
    """Schema for gas consumption response."""
    
    id: int
    tank_id: int
    quantity_consumed_kg: Optional[Decimal]
    quantity_consumed_m3: Optional[Decimal]
    production_batch_id: Optional[int]
    purpose: str
    notes: Optional[str]
    consumed_at: datetime
    recorded_by: Optional[str]
    
    class Config:
        from_attributes = True
