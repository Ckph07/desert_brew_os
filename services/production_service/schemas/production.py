"""
Pydantic schemas for Production Service.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal


# Recipe Schemas

class RecipeIngredientSummary(BaseModel):
    """Summary of recipe ingredients for display."""
    total_fermentables_kg: float
    total_hops_g: float
    yeast_count: int


class RecipeResponse(BaseModel):
    """Recipe response."""
    id: int
    name: str
    style: Optional[str]
    batch_size_liters: float
    fermentables: List[Dict]
    hops: List[Dict]
    yeast: List[Dict]
    expected_og: Optional[float]
    expected_fg: Optional[float]
    expected_abv: Optional[float]
    ibu: Optional[float]
    color_srm: Optional[float]
    brewhouse_efficiency: Optional[float]
    imported_at: datetime
    
    class Config:
        orm_mode = True


# Production Batch Schemas

class CreateBatchRequest(BaseModel):
    """Request to create a new production batch."""
    recipe_id: int = Field(..., description="Recipe to use for this batch")
    batch_number: str = Field(..., min_length=1, max_length=50, description="Unique batch number (e.g. IPA-2026-001)")
    planned_volume_liters: float = Field(..., gt=0, description="Planned batch volume in liters")
    notes: Optional[str] = Field(None, max_length=1000)
    created_by_user_id: Optional[int] = None


class UpdateBatchVolumeRequest(BaseModel):
    """Update actual volume after packaging."""
    actual_volume_liters: float = Field(..., gt=0, description="Actual volume produced")
    actual_og: Optional[float] = Field(None, description="Measured Original Gravity")
    actual_fg: Optional[float] = Field(None, description="Measured Final Gravity")


class BatchResponse(BaseModel):
    """Production batch response."""
    id: int
    batch_number: str
    recipe_id: int
    recipe_name: str
    status: str
    planned_volume_liters: float
    actual_volume_liters: Optional[float]
    total_cost: Optional[float]
    cost_per_liter: Optional[float]
    planned_at: datetime
    brewing_started_at: Optional[datetime]
    fermenting_started_at: Optional[datetime]
    conditioning_started_at: Optional[datetime]
    packaging_started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class BatchDetailResponse(BatchResponse):
    """Detailed batch response with cost breakdown."""
    malt_cost: Optional[float]
    hops_cost: Optional[float]
    yeast_cost: Optional[float]
    water_cost: Optional[float]
    labor_cost: Optional[float]
    overhead_cost: Optional[float]
    actual_og: Optional[float]
    actual_fg: Optional[float]
    actual_abv: Optional[float]
    yield_percentage: Optional[float]
    days_in_production: Optional[int]
    notes: Optional[str]


class CostBreakdownResponse(BaseModel):
    """Cost allocation breakdown."""
    batch_id: int
    batch_number: str
    total_cost: float
    cost_per_liter: float
    breakdown: Dict[str, float]  # {'malt': 100, 'hops': 50, ...}
    allocations: List[Dict]  # Ingredient-level allocations


class BatchTransitionResponse(BaseModel):
    """Response after state transition."""
    batch_id: int
    batch_number: str
    previous_status: str
    new_status: str
    timestamp: datetime
    message: str
