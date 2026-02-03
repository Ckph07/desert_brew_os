"""
Pydantic schemas for supplier management.
"""
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal
from datetime import datetime
from typing import Optional


class SupplierCreate(BaseModel):
    """Schema for creating a new supplier."""
    
    name: str = Field(..., min_length=1, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=300)
    rfc: Optional[str] = Field(None, max_length=20, description="Tax ID (RFC)")
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=200)
    
    payment_terms: Optional[str] = Field(None, max_length=100, description="e.g., '30 días', 'Contado'")
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    
    preferred: bool = Field(default=False)
    notes: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Malterías Tepeyac",
                "legal_name": "Malterías Tepeyac S.A. de C.V.",
                "rfc": "MTE850101ABC",
                "email": "ventas@tepeyac.com.mx",
                "phone": "+52 81 8888 9999",
                "address": "Av. Industrial 123, Monterrey, NL",
                "contact_person": "Juan Pérez",
                "payment_terms": "30 días",
                "credit_limit": 50000.00,
                "preferred": True
            }
        }


class SupplierUpdate(BaseModel):
    """Schema for updating supplier information."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=300)
    rfc: Optional[str] = Field(None, max_length=20)
    
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    contact_person: Optional[str] = Field(None, max_length=200)
    
    payment_terms: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    
    is_active: Optional[bool] = None
    preferred: Optional[bool] = None
    
    quality_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    delivery_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    
    notes: Optional[str] = Field(None, max_length=1000)


class SupplierResponse(BaseModel):
    """Schema for supplier response."""
    
    id: int
    name: str
    legal_name: Optional[str]
    rfc: Optional[str]
    
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    contact_person: Optional[str]
    
    payment_terms: Optional[str]
    credit_limit: Optional[Decimal]
    
    is_active: bool
    preferred: bool
    
    quality_rating: Optional[Decimal]
    delivery_rating: Optional[Decimal]
    
    notes: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SupplierSummary(BaseModel):
    """Lightweight supplier info for listings."""
    
    id: int
    name: str
    rfc: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    is_active: bool
    preferred: bool
    quality_rating: Optional[Decimal]
    
    class Config:
        from_attributes = True
