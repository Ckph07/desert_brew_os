"""
Pydantic schemas for Product Catalog CRUD.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    sku: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    style: Optional[str] = Field(None, max_length=100)
    category: str = Field(..., max_length=30)
    origin_type: str = Field("HOUSE", pattern="^(HOUSE|GUEST|COMMERCIAL)$")
    volume_ml: Optional[int] = Field(None, ge=0)
    unit_measure: str = Field("LITROS", max_length=20)
    abv: Optional[float] = Field(None, ge=0, le=100)
    ibu: Optional[int] = Field(None, ge=0)
    # Dual pricing
    fixed_price: Optional[float] = Field(None, ge=0)
    theoretical_price: Optional[float] = Field(None, ge=0)
    cost_per_unit: Optional[float] = Field(None, ge=0)
    # Channel pricing
    price_taproom: Optional[float] = Field(None, ge=0)
    price_distributor: Optional[float] = Field(None, ge=0)
    price_on_premise: Optional[float] = Field(None, ge=0)
    price_off_premise: Optional[float] = Field(None, ge=0)
    price_ecommerce: Optional[float] = Field(None, ge=0)
    # Tax
    ieps_rate: Optional[float] = Field(None, ge=0)
    iva_rate: Optional[float] = Field(0.16, ge=0)
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "sku": "BEER-IPA-COAHUI-L",
                "product_name": "Litro Coahuilaceratops (Imperial Indian Pale Ale)",
                "style": "Imperial IPA",
                "category": "BEER_LITER",
                "origin_type": "HOUSE",
                "unit_measure": "LITROS",
                "abv": 7.2,
                "ibu": 75,
                "fixed_price": 109.44,
                "theoretical_price": 95.00,
                "cost_per_unit": 21.54,
                "price_taproom": 130.00,
                "price_distributor": 109.44,
                "price_on_premise": 115.00
            }
        }


class ProductUpdate(BaseModel):
    """Schema for updating a product (all fields optional)."""
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    style: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=30)
    origin_type: Optional[str] = Field(None, pattern="^(HOUSE|GUEST|COMMERCIAL)$")
    volume_ml: Optional[int] = Field(None, ge=0)
    unit_measure: Optional[str] = Field(None, max_length=20)
    abv: Optional[float] = Field(None, ge=0, le=100)
    ibu: Optional[int] = Field(None, ge=0)
    fixed_price: Optional[float] = Field(None, ge=0)
    theoretical_price: Optional[float] = Field(None, ge=0)
    cost_per_unit: Optional[float] = Field(None, ge=0)
    price_taproom: Optional[float] = Field(None, ge=0)
    price_distributor: Optional[float] = Field(None, ge=0)
    price_on_premise: Optional[float] = Field(None, ge=0)
    price_off_premise: Optional[float] = Field(None, ge=0)
    price_ecommerce: Optional[float] = Field(None, ge=0)
    ieps_rate: Optional[float] = Field(None, ge=0)
    iva_rate: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class ChannelPriceUpdate(BaseModel):
    """Schema for updating prices per channel (logs to PriceHistory)."""
    price_taproom: Optional[float] = Field(None, ge=0)
    price_distributor: Optional[float] = Field(None, ge=0)
    price_on_premise: Optional[float] = Field(None, ge=0)
    price_off_premise: Optional[float] = Field(None, ge=0)
    price_ecommerce: Optional[float] = Field(None, ge=0)
    fixed_price: Optional[float] = Field(None, ge=0)
    change_reason: Optional[str] = Field(None, max_length=200)
    changed_by: Optional[str] = Field(None, max_length=100)


class ProductResponse(BaseModel):
    """Full product response with margin calculations."""
    id: int
    sku: str
    product_name: str
    description: Optional[str] = None
    style: Optional[str] = None
    category: str
    origin_type: str
    volume_ml: Optional[int] = None
    unit_measure: str
    abv: Optional[float] = None
    ibu: Optional[int] = None
    # Dual pricing
    fixed_price: Optional[float] = None
    theoretical_price: Optional[float] = None
    cost_per_unit: Optional[float] = None
    # Margins (calculated)
    fixed_margin_pct: Optional[float] = None
    theoretical_margin_pct: Optional[float] = None
    margin_delta_pct: Optional[float] = None
    # Channel pricing
    price_taproom: Optional[float] = None
    price_distributor: Optional[float] = None
    price_on_premise: Optional[float] = None
    price_off_premise: Optional[float] = None
    price_ecommerce: Optional[float] = None
    # Tax
    ieps_rate: Optional[float] = None
    iva_rate: Optional[float] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Price change record."""
    id: int
    product_id: int
    channel: str
    old_price: Optional[float] = None
    new_price: float
    change_reason: Optional[str] = None
    changed_by: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


class MarginReportItem(BaseModel):
    """Single product in the margin comparison report."""
    id: int
    sku: str
    product_name: str
    category: str
    origin_type: str
    cost_per_unit: Optional[float] = None
    fixed_price: Optional[float] = None
    theoretical_price: Optional[float] = None
    fixed_margin_pct: Optional[float] = None
    theoretical_margin_pct: Optional[float] = None
    margin_delta_pct: Optional[float] = None
    price_distributor: Optional[float] = None
    price_taproom: Optional[float] = None


class MarginReportResponse(BaseModel):
    """Margin comparison report: fixed vs theoretical."""
    products: list[MarginReportItem]
    total_products: int
    avg_fixed_margin: Optional[float] = None
    avg_theoretical_margin: Optional[float] = None
