"""
Pydantic schemas for Inventory Service API.
"""
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum


class UnitMeasure(str, Enum):
    """Valid unit measures for inventory."""
    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"
    UNIT = "UNIT"


class IngredientCategory(str, Enum):
    """Categories of ingredients."""
    MALT = "MALT"
    HOPS = "HOPS"
    YEAST = "YEAST"
    BOTTLE = "BOTTLE"
    CAP = "CAP"
    CHEMICAL = "CHEMICAL"
    LABEL = "LABEL"
    OTHER = "OTHER"


class StockBatchCreate(BaseModel):
    """Schema for creating a new stock batch (receiving inventory)."""
    
    sku: str = Field(..., min_length=3, max_length=50, description="Product SKU")
    batch_number: Optional[str] = Field(None, max_length=100, description="Supplier batch number")
    category: IngredientCategory
    
    quantity: Decimal = Field(..., gt=0, description="Quantity received")
    unit_measure: UnitMeasure
    
    unit_cost: Decimal = Field(..., gt=0, description="Cost per unit in MXN")
    
    provider_name: Optional[str] = Field(None, max_length=200)
    invoice_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100, description="Storage location")
    
    expiration_date: Optional[datetime] = None
    
    @field_validator('sku')
    @classmethod
    def sku_uppercase(cls, v: str) -> str:
        """Ensure SKU is uppercase."""
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "sku": "MALT-PALE-2ROW",
                "batch_number": "LOT-2026-005",
                "category": "MALT",
                "quantity": 250.0,
                "unit_measure": "KG",
                "unit_cost": 18.50,
                "provider_name": "Malterías Tepeyac",
                "location": "Silo A"
            }
        }


class StockBatchResponse(BaseModel):
    """Schema for StockBatch response."""
    
    id: int
    sku: str
    batch_number: Optional[str]
    category: str
    
    arrival_date: datetime
    expiration_date: Optional[datetime]
    
    initial_quantity: Decimal
    remaining_quantity: Decimal
    unit_measure: str
    
    unit_cost: Decimal
    total_cost: Decimal
    
    provider_name: Optional[str]
    location: Optional[str]
    
    is_allocated: bool
    utilization_percentage: float
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockAllocationRequest(BaseModel):
    """Request to allocate stock using FIFO."""
    
    sku: str = Field(..., min_length=3)
    amount_needed: Decimal = Field(..., gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sku": "HOPS-CASCADE",
                "amount_needed": 100.5
            }
        }


class StockAllocationResponse(BaseModel):
    """Response from FIFO allocation."""
    
    sku: str
    total_allocated: Decimal
    allocations: list[dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "sku": "HOPS-CASCADE",
                "total_allocated": 100.5,
                "allocations": [
                    {
                        "batch_id": 101,
                        "batch_number": "LOT-2025-12",
                        "quantity": 50.0,
                        "unit_cost": 120.00,
                        "total_cost": 6000.00
                    },
                    {
                        "batch_id": 105,
                        "batch_number": "LOT-2026-01",
                        "quantity": 50.5,
                        "unit_cost": 125.00,
                        "total_cost": 6312.50
                    }
                ]
            }
        }
