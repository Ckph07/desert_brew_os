"""
Pydantic schemas for Production Service.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal


# Recipe Schemas

class FermentableInput(BaseModel):
    """Fermentable ingredient input."""
    name: str = Field(..., min_length=1, max_length=100)
    amount_kg: float = Field(..., gt=0)
    color_srm: Optional[float] = None
    type: Optional[str] = Field(None, description="Grain, Sugar, Extract, Dry Extract, Adjunct")


class HopInput(BaseModel):
    """Hop ingredient input."""
    name: str = Field(..., min_length=1, max_length=100)
    amount_g: float = Field(..., gt=0)
    time_min: Optional[float] = Field(None, ge=0)
    use: Optional[str] = Field("Boil", description="Boil, Dry Hop, First Wort, Whirlpool")
    alpha_acid: Optional[float] = None


class YeastInput(BaseModel):
    """Yeast input."""
    name: str = Field(..., min_length=1, max_length=100)
    lab: Optional[str] = Field(None, max_length=100)
    product_id: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None, description="Ale, Lager, Wheat, Wine, Champagne")


class MashStepInput(BaseModel):
    """Mash step input."""
    step: str = Field(..., min_length=1, max_length=100)
    temp_c: float = Field(..., gt=0)
    time_min: float = Field(..., gt=0)


class CreateRecipeRequest(BaseModel):
    """Request to create a recipe manually."""
    name: str = Field(..., min_length=1, max_length=200)
    style: Optional[str] = Field(None, max_length=100)
    brewer: Optional[str] = Field(None, max_length=100)
    batch_size_liters: float = Field(..., gt=0)
    fermentables: List[FermentableInput] = Field(..., min_length=1)
    hops: List[HopInput] = Field(default=[])
    yeast: List[YeastInput] = Field(..., min_length=1)
    water_profile: Optional[Dict] = None
    mash_steps: Optional[List[MashStepInput]] = None
    expected_og: Optional[float] = Field(None, gt=0)
    expected_fg: Optional[float] = Field(None, gt=0)
    expected_abv: Optional[float] = Field(None, ge=0)
    ibu: Optional[float] = Field(None, ge=0)
    color_srm: Optional[float] = Field(None, ge=0)
    brewhouse_efficiency: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=2000)


class UpdateRecipeRequest(BaseModel):
    """Request to update a recipe."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    style: Optional[str] = Field(None, max_length=100)
    brewer: Optional[str] = Field(None, max_length=100)
    batch_size_liters: Optional[float] = Field(None, gt=0)
    fermentables: Optional[List[FermentableInput]] = None
    hops: Optional[List[HopInput]] = None
    yeast: Optional[List[YeastInput]] = None
    water_profile: Optional[Dict] = None
    mash_steps: Optional[List[MashStepInput]] = None
    expected_og: Optional[float] = Field(None, gt=0)
    expected_fg: Optional[float] = Field(None, gt=0)
    expected_abv: Optional[float] = Field(None, ge=0)
    ibu: Optional[float] = Field(None, ge=0)
    color_srm: Optional[float] = Field(None, ge=0)
    brewhouse_efficiency: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=2000)


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
    brewer: Optional[str] = None
    batch_size_liters: float
    fermentables: List[Dict]
    hops: List[Dict]
    yeast: List[Dict]
    water_profile: Optional[Dict] = None
    mash_steps: Optional[List[Dict]] = None
    expected_og: Optional[float]
    expected_fg: Optional[float]
    expected_abv: Optional[float]
    ibu: Optional[float]
    color_srm: Optional[float] = None
    brewhouse_efficiency: Optional[float]
    notes: Optional[str] = None
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
