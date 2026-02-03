"""
Pydantic schemas for Finished Product Inventory.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from models.finished_product_enums import (
    ProductType,
    ProductCategory,
    AvailabilityStatus,
    MovementType,
    ColdRoomLocation
)


# ==================== CREATE SCHEMAS ====================

class FinishedProductCreate(BaseModel):
    """Schema for creating a finished product."""
    sku: str = Field(..., max_length=100, description="Product SKU")
    product_name: str = Field(..., max_length=200, description="Product name")
    product_type: ProductType
    category: ProductCategory
    
    # Optional trazabilidad fields
    production_batch_id: Optional[int] = Field(None, description="Production batch ID (for own beer)")
    supplier_id: Optional[int] = Field(None, description="Supplier ID (for commercial)")
    guest_brewery_id: Optional[int] = Field(None, description="Guest brewery ID")
    keg_asset_id: Optional[str] = Field(None, description="Keg asset UUID (if BEER_KEG)")
    
    # Quantity
    quantity: Decimal = Field(..., ge=0, description="Quantity")
    unit_measure: str = Field(..., max_length=20, description="Unit (BOTTLES, KEGS, CANS, UNITS)")
    
    # Location
    cold_room_id: ColdRoomLocation
    shelf_position: Optional[str] = Field(None, max_length=10, description="Shelf position (A3, B12)")
    
    # Cost
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost")
    
    # Dates
    production_date: Optional[datetime] = None
    best_before: Optional[datetime] = None
    
    # Additional
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('production_batch_id')
    def validate_own_production_has_batch(cls, v, values):
        """Validate that own production has batch_id."""
        if values.get('product_type') == ProductType.OWN_PRODUCTION and not v:
            raise ValueError('Own production must have production_batch_id')
        return v
    
    @validator('supplier_id')
    def validate_commercial_has_supplier(cls, v, values):
        """Validate that commercial products have supplier."""
        if values.get('product_type') in [ProductType.COMMERCIAL, ProductType.GUEST_CRAFT] and not v:
            raise ValueError('Commercial/Guest products must have supplier_id')
        return v


class FinishedProductUpdate(BaseModel):
    """Schema for updating finished product (location, status)."""
    cold_room_id: Optional[ColdRoomLocation] = None
    shelf_position: Optional[str] = Field(None, max_length=10)
    availability_status: Optional[AvailabilityStatus] = None
    notes: Optional[str] = Field(None, max_length=500)


# ==================== RESPONSE SCHEMAS ====================

class FinishedProductResponse(BaseModel):
    """Response schema for finished product."""
    id: int
    sku: str
    product_name: str
    product_type: str
    category: str
    
    # Trazabilidad
    production_batch_id: Optional[int]
    supplier_id: Optional[int]
    guest_brewery_id: Optional[int]
    keg_asset_id: Optional[str]
    
    # Quantity
    quantity: Decimal
    unit_measure: str
    
    # Location
    cold_room_id: str
    shelf_position: Optional[str]
    
    # Cost
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]
    
    # Dates
    received_date: datetime
    production_date: Optional[datetime]
    best_before: Optional[datetime]
    
    # Status
    availability_status: str
    
    # Additional
    notes: Optional[str]
    
    # Audit
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_available: bool
    value: Decimal
    
    class Config:
        from_attributes = True


class FinishedProductWithMovements(FinishedProductResponse):
    """Finished product with movement history."""
    movements: List['ProductMovementResponse'] = []


# ==================== MOVEMENT SCHEMAS ====================

class ProductMovementCreate(BaseModel):
    """Schema for creating a product movement."""
    finished_product_id: int
    movement_type: MovementType
    quantity: Decimal = Field(..., ge=0)
    
    from_location: Optional[str] = Field(None, max_length=50)
    to_location: Optional[str] = Field(None, max_length=50)
    
    sales_order_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    user_id: Optional[int] = None
    
    notes: Optional[str] = Field(None, max_length=500)
    reference_number: Optional[str] = Field(None, max_length=50)


class ProductMovementResponse(BaseModel):
    """Response schema for product movement."""
    id: int
    finished_product_id: int
    movement_type: str
    quantity: Decimal
    
    from_location: Optional[str]
    to_location: Optional[str]
    
    sales_order_id: Optional[int]
    purchase_order_id: Optional[int]
    user_id: Optional[int]
    
    notes: Optional[str]
    reference_number: Optional[str]
    
    timestamp: datetime
    
    is_ingress: bool
    is_egress: bool
    
    class Config:
        from_attributes = True


class ProductMoveRequest(BaseModel):
    """Request to move product between locations."""
    quantity: Decimal = Field(..., gt=0, description="Quantity to move")
    to_location: ColdRoomLocation = Field(..., description="Destination")
    to_shelf: Optional[str] = Field(None, max_length=10, description="Destination shelf")
    user_id: int = Field(..., description="User performing move")
    notes: Optional[str] = Field(None, max_length=500)


# ==================== COLD ROOM SCHEMAS ====================

class ColdRoomReadingCreate(BaseModel):
    """Schema for creating a cold room temperature reading."""
    cold_room_id: ColdRoomLocation
    temperature_celsius: Decimal = Field(..., ge=-10, le=20, description="Temperature in Celsius")
    humidity_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="Humidity percentage")


class ColdRoomReadingResponse(BaseModel):
    """Response schema for cold room reading."""
    id: int
    cold_room_id: str
    temperature_celsius: Decimal
    humidity_percent: Optional[Decimal]
    alert_triggered: bool
    alert_reason: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ColdRoomStatus(BaseModel):
    """Current status of a cold room."""
    id: str
    current_temp: Decimal
    target_temp: Decimal = Decimal('4.0')
    last_reading: datetime
    alert_active: bool
    utilization_percent: Optional[Decimal] = None


class ColdRoomStatusResponse(BaseModel):
    """Response with all cold rooms status."""
    cold_rooms: List[ColdRoomStatus]


# ==================== SUMMARY & REPORTS ====================

class ProductTypeSummary(BaseModel):
    """Summary for a product category."""
    quantity: Decimal
    value: Decimal


class StockSummaryResponse(BaseModel):
    """Stock summary by product type and category."""
    own_production: Dict[str, ProductTypeSummary] = {}
    commercial: Dict[str, ProductTypeSummary] = {}
    guest_craft: Dict[str, ProductTypeSummary] = {}
    merchandise: Dict[str, ProductTypeSummary] = {}
    total_items: Decimal
    total_value: Decimal


class SlowMovingProduct(BaseModel):
    """Slow-moving product report item."""
    id: int
    sku: str
    product_name: str
    category: str
    quantity: Decimal
    cold_room_id: str
    last_movement: Optional[datetime]
    days_without_movement: Optional[int]
    value: Decimal


class SlowMovingReportResponse(BaseModel):
    """Response for slow-moving products report."""
    products: List[SlowMovingProduct]
    total_value_at_risk: Decimal


# ==================== FILTERS ====================

class FinishedProductFilters(BaseModel):
    """Query filters for listing finished products."""
    product_type: Optional[ProductType] = None
    category: Optional[ProductCategory] = None
    cold_room_id: Optional[ColdRoomLocation] = None
    availability_status: Optional[AvailabilityStatus] = None
    production_batch_id: Optional[int] = None
    supplier_id: Optional[int] = None
    
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=500)


# Update forward references
FinishedProductWithMovements.model_rebuild()
