"""
Pydantic schemas for ingredient catalog endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from schemas.stock import IngredientCategory, UnitMeasure


class IngredientCatalogCreate(BaseModel):
    """Create schema for catalog ingredient."""

    name: str = Field(..., min_length=2, max_length=120)
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    category: IngredientCategory
    unit_measure: UnitMeasure
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip().upper()


class IngredientCatalogUpdate(BaseModel):
    """Partial update schema for catalog ingredient."""

    name: Optional[str] = Field(None, min_length=2, max_length=120)
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    category: Optional[IngredientCategory] = None
    unit_measure: Optional[UnitMeasure] = None
    notes: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip()

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip().upper()


class IngredientCatalogResponse(BaseModel):
    """Response schema for ingredient catalog item."""

    id: int
    sku: str
    name: str
    category: str
    unit_measure: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
