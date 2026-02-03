"""
API routes for supplier management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from database import get_db
from models.supplier import Supplier
from schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierSummary
)

router = APIRouter()


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new supplier.
    
    Registers a new raw material or ingredient supplier in the system.
    """
    # Create supplier
    new_supplier = Supplier(
        name=supplier.name,
        legal_name=supplier.legal_name,
        rfc=supplier.rfc,
        email=supplier.email,
        phone=supplier.phone,
        address=supplier.address,
        contact_person=supplier.contact_person,
        payment_terms=supplier.payment_terms,
        credit_limit=supplier.credit_limit,
        preferred=supplier.preferred,
        notes=supplier.notes,
    )
    
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    
    return new_supplier


@router.get("/suppliers", response_model=list[SupplierSummary])
async def list_suppliers(
    active_only: bool = Query(True, description="Only show active suppliers"),
    preferred_only: bool = Query(False, description="Only show preferred suppliers"),
    search: Optional[str] = Query(None, description="Search by name or RFC"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List suppliers with optional filters.
    
    Supports filtering by active status, preferred flag, and text search.
    """
    query = select(Supplier)
    
    # Apply filters
    if active_only:
        query = query.where(Supplier.is_active == True)
    
    if preferred_only:
        query = query.where(Supplier.preferred == True)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Supplier.name.ilike(search_pattern)) |
            (Supplier.rfc.ilike(search_pattern))
        )
    
    # Order and paginate
    query = query.order_by(Supplier.preferred.desc(), Supplier.name.asc())
    query = query.offset(skip).limit(limit)
    
    suppliers = db.execute(query).scalars().all()
    return suppliers


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific supplier."""
    supplier = db.get(Supplier, supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int,
    updates: SupplierUpdate,
    db: Session = Depends(get_db)
):
    """
    Update supplier information.
    
    Can update contact info, ratings, payment terms, etc.
    """
    supplier = db.get(Supplier, supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    # Apply updates (only non-None fields)
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.delete("/suppliers/{supplier_id}")
async def deactivate_supplier(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    """
    Deactivate a supplier (soft delete).
    
    Sets is_active to False instead of deleting the record.
    """
    supplier = db.get(Supplier, supplier_id)
    
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    supplier.is_active = False
    db.commit()
    
    return {
        "message": f"Supplier '{supplier.name}' deactivated successfully",
        "id": supplier_id
    }


@router.get("/suppliers/{supplier_id}/stock-batches")
async def get_supplier_batches(
    supplier_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all stock batches from a specific supplier.
    
    Useful for quality tracking and supplier performance analysis.
    """
    from models.stock import StockBatch
    
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    batches = db.execute(
        select(StockBatch)
        .where(StockBatch.supplier_id == supplier_id)
        .order_by(StockBatch.arrival_date.desc())
        .limit(100)
    ).scalars().all()
    
    return {
        "supplier_name": supplier.name,
        "total_batches": len(batches),
        "batches": batches
    }
