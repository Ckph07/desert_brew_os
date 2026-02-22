"""
Pydantic schemas for Client CRUD.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClientCreate(BaseModel):
    """Schema for creating a new client."""
    business_name: str = Field(..., min_length=1, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=300)
    rfc: Optional[str] = Field(None, max_length=20)
    client_type: str = Field("B2B", pattern="^(B2B|B2C|DISTRIBUTOR)$")
    pricing_tier: str = Field("RETAIL", pattern="^(PLATINUM|GOLD|SILVER|RETAIL)$")
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    credit_limit: Optional[float] = Field(None, ge=0)
    max_kegs: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "business_name": "Bar La Herradura",
                "legal_name": "La Herradura SA de CV",
                "rfc": "HER200101ABC",
                "client_type": "B2B",
                "pricing_tier": "GOLD",
                "email": "contacto@laherradura.mx",
                "phone": "+52 844 123 4567",
                "address": "Blvd. V. Carranza 1234, Saltillo",
                "city": "Saltillo",
                "state": "Coahuila",
                "contact_person": "Juan Pérez",
                "credit_limit": 50000.00,
                "max_kegs": 10
            }
        }


class ClientUpdate(BaseModel):
    """Schema for updating a client (all fields optional)."""
    business_name: Optional[str] = Field(None, min_length=1, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=300)
    rfc: Optional[str] = Field(None, max_length=20)
    client_type: Optional[str] = Field(None, pattern="^(B2B|B2C|DISTRIBUTOR)$")
    pricing_tier: Optional[str] = Field(None, pattern="^(PLATINUM|GOLD|SILVER|RETAIL)$")
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    credit_limit: Optional[float] = Field(None, ge=0)
    max_kegs: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    """Schema for client responses."""
    id: int
    client_code: str
    business_name: str
    legal_name: Optional[str] = None
    rfc: Optional[str] = None
    client_type: str
    pricing_tier: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact_person: Optional[str] = None
    credit_limit: Optional[float] = None
    current_balance: float
    max_kegs: Optional[int] = None
    current_kegs: int
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientBalanceResponse(BaseModel):
    """Client balance and credit status."""
    client_id: int
    client_code: str
    business_name: str
    credit_limit: Optional[float] = None
    current_balance: float
    available_credit: float
    max_kegs: Optional[int] = None
    current_kegs: int
    available_kegs: int
    can_order: bool
    blocking_reasons: list[str] = []
