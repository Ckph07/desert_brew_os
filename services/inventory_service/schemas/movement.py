"""
Pydantic schemas for stock transfers and movements.
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from models.enums import MovementType, MovementOrigin, TransferStatus


class StockTransferCreate(BaseModel):
    """Request to transfer stock between locations."""
    
    sku: str = Field(..., min_length=3, description="Product SKU")
    quantity: Decimal = Field(..., gt=0, description="Amount to transfer")
    from_location: str = Field(..., min_length=1, description="Source location")
    to_location: str = Field(..., min_length=1, description="Destination location")
    notes: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sku": "MALT-PALE-2ROW",
                "quantity": 50.0,
                "from_location": "Silo A",
                "to_location": "Silo B",
                "notes": "Reorganizando almacén"
            }
        }


class StockTransferResponse(BaseModel):
    """Response for stock transfer."""
    
    id: int
    sku: str
    quantity: Decimal
    unit_measure: str
    from_location: str
    to_location: str
    status: str
    requested_at: datetime
    completed_at: Optional[datetime]
    requested_by: Optional[str]
    executed_by: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class StockMovementResponse(BaseModel):
    """Response for movement history."""
    
    id: int
    sku: str
    movement_type: str
    movement_origin: Optional[str]
    quantity: Decimal
    unit_measure: str
    from_location: Optional[str]
    to_location: Optional[str]
    reference: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockAdjustmentCreate(BaseModel):
    """Manual stock adjustment (waste, count correction, etc.)."""
    
    sku: str = Field(..., min_length=3)
    quantity: Decimal = Field(..., description="Positive for increase, negative for decrease")
    movement_type: MovementType
    movement_origin: MovementOrigin
    location: Optional[str] = None
    reference: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sku": "HOPS-CASCADE",
                "quantity": -5.0,
                "movement_type": "WASTE",
                "movement_origin": "QUALITY_ISSUE",
                "reference": "QC-2026-015",
                "notes": "Lote con moho detectado en inspección"
            }
        }
