"""
Pydantic schemas for Ingredient Prices and Fixed Monthly Costs.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# === Ingredient Price Schemas ===

class IngredientPriceCreate(BaseModel):
    """Schema for creating an ingredient price entry."""
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., max_length=50)
    # MALT, HOP, YEAST, ADJUNCT, CHEMICAL, PACKAGING, OTHER
    unit_measure: str = Field(..., max_length=20)
    # KG, G, L, ML, PACKET, UNIT
    current_price: float = Field(..., gt=0)
    currency: str = Field("MXN", max_length=3)
    supplier_name: Optional[str] = Field(None, max_length=200)
    supplier_sku: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Malt",
                    "value": {
                        "name": "Malta Pale Ale / Pilsen",
                        "category": "MALT",
                        "unit_measure": "KG",
                        "current_price": 25.80,
                        "supplier_name": "Malteurop",
                    },
                },
                {
                    "summary": "Hop",
                    "value": {
                        "name": "Cryo Mosaic",
                        "category": "HOP",
                        "unit_measure": "G",
                        "current_price": 2.16,
                    },
                },
            ]
        }


class IngredientPriceUpdate(BaseModel):
    """Schema for updating an ingredient price."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    unit_measure: Optional[str] = Field(None, max_length=20)
    current_price: Optional[float] = Field(None, gt=0)
    supplier_name: Optional[str] = Field(None, max_length=200)
    supplier_sku: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class IngredientPriceResponse(BaseModel):
    """Ingredient price response."""
    id: int
    name: str
    category: str
    unit_measure: str
    current_price: float
    currency: str
    supplier_name: Optional[str] = None
    supplier_sku: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    last_price_update: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Fixed Monthly Cost Schemas ===

class FixedMonthlyCostCreate(BaseModel):
    """Schema for creating a fixed cost line item."""
    category: str = Field(..., max_length=50)
    # FUEL, ENERGY, WATER, HR, OPERATIONS, GAS_CO2, COMMS, VEHICLE, OTHER
    concept: str = Field(..., min_length=1, max_length=200)
    monthly_amount: float = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=500)


class FixedMonthlyCostUpdate(BaseModel):
    """Schema for updating a fixed cost."""
    category: Optional[str] = Field(None, max_length=50)
    concept: Optional[str] = Field(None, min_length=1, max_length=200)
    monthly_amount: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class FixedMonthlyCostResponse(BaseModel):
    """Fixed cost line item response."""
    id: int
    category: str
    concept: str
    monthly_amount: float
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Production Target Schemas ===

class ProductionTargetCreate(BaseModel):
    """Schema for setting production target."""
    period: str = Field(..., max_length=10, description="e.g. '2026-02' or 'DEFAULT'")
    target_liters_monthly: float = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=500)


class ProductionTargetResponse(BaseModel):
    """Production target response."""
    id: int
    period: str
    target_liters_monthly: float
    total_fixed_cost: Optional[float] = None
    fixed_cost_per_liter: Optional[float] = None
    is_current: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Summary Schemas ===

class CostSummaryResponse(BaseModel):
    """Consolidated cost summary."""
    total_fixed_monthly: float
    target_liters: float
    fixed_cost_per_liter: float
    cost_breakdown: list[dict]
    ingredient_count: int
    ingredient_total_estimated: Optional[float] = None
