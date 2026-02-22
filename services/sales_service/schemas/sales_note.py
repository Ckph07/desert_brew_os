"""
Pydantic schemas for Sales Notes CRUD.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SalesNoteItemCreate(BaseModel):
    """Schema for a line item when creating a note."""
    product_id: Optional[int] = None
    sku: Optional[str] = Field(None, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=200)
    unit_measure: str = Field("LITROS", max_length=20)
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    discount_pct: float = Field(0, ge=0, le=100)
    ieps_rate: float = Field(0, ge=0)
    iva_rate: float = Field(0.16, ge=0)


class SalesNoteCreate(BaseModel):
    """Schema for creating a sales note."""
    client_id: Optional[int] = None
    client_name: Optional[str] = Field(None, max_length=200)
    channel: str = Field("B2B", max_length=20)
    payment_method: str = Field("TRANSFERENCIA", max_length=30)
    include_taxes: bool = Field(False, description="When False, IEPS/IVA shown as empty (not invoiced)")
    notes: Optional[str] = Field(None, max_length=500)
    created_by: Optional[str] = Field(None, max_length=100)
    items: list[SalesNoteItemCreate] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": 1,
                "client_name": "Hop Experience",
                "channel": "B2B",
                "payment_method": "TRANSFERENCIA",
                "include_taxes": False,
                "items": [
                    {
                        "product_name": "Litro Carnotaurus (Amber Lager)",
                        "unit_measure": "LITROS",
                        "quantity": 18,
                        "unit_price": 77.44,
                    },
                    {
                        "product_name": "Litro Coahuilaceratops (Imperial Indian Pale Ale)",
                        "unit_measure": "LITROS",
                        "quantity": 18,
                        "unit_price": 109.44,
                    },
                    {
                        "product_name": "Barril Desechable 20L",
                        "unit_measure": "UNITS",
                        "quantity": 2,
                        "unit_price": 589.00,
                    },
                    {
                        "product_name": "Envío",
                        "unit_measure": "UNITS",
                        "quantity": 2,
                        "unit_price": 285.00,
                    },
                ],
            }
        }


class SalesNoteUpdate(BaseModel):
    """Schema for updating a DRAFT sales note."""
    client_id: Optional[int] = None
    client_name: Optional[str] = Field(None, max_length=200)
    payment_method: Optional[str] = Field(None, max_length=30)
    include_taxes: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class SalesNoteItemResponse(BaseModel):
    """Line item response."""
    id: int
    product_id: Optional[int] = None
    sku: Optional[str] = None
    product_name: str
    unit_measure: str
    quantity: float
    unit_price: float
    discount_pct: float
    subtotal: float
    ieps_amount: float
    iva_amount: float
    line_total: float

    class Config:
        from_attributes = True


class SalesNoteResponse(BaseModel):
    """Full sales note response."""
    id: int
    note_number: str
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    issuer_name: str
    issuer_rfc: str
    issuer_address: str
    issuer_phone: str
    include_taxes: bool
    subtotal: float
    ieps_total: float
    iva_total: float
    total: float
    total_liters: float
    channel: str
    payment_method: str
    payment_status: str
    status: str
    notes: Optional[str] = None
    created_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: list[SalesNoteItemResponse] = []

    class Config:
        from_attributes = True
