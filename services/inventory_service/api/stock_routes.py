"""
API routes for stock management.

Endpoints:
- POST /stock - Receive new inventory
- GET /stock/{sku} - Get stock for specific SKU
- GET /stock - List all stock with filters
- POST /allocate - Allocate stock using FIFO
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
from typing import Optional
from datetime import datetime

from database import get_db
from models.stock import StockBatch
from schemas.stock import (
    StockBatchCreate,
    StockBatchResponse,
    StockAllocationRequest,
    StockAllocationResponse,
    IngredientCategory
)
from logic.stock_rotation import allocate_stock_fifo, InsufficientStockError

router = APIRouter()


@router.post("/stock", response_model=StockBatchResponse, status_code=201)
async def receive_stock(
    stock: StockBatchCreate,
    db: Session = Depends(get_db)
):
    """
    Recibir nuevo inventario de materia prima.
    
    Este endpoint se usa cuando llega un envío del proveedor.
    Crea un nuevo batch en el sistema con trazabilidad completa.
    """
    # Calculate total cost
    total_cost = stock.quantity * stock.unit_cost
    
    # Create new StockBatch
    new_batch = StockBatch(
        sku=stock.sku,
        batch_number=stock.batch_number,
        category=stock.category.value,
        initial_quantity=stock.quantity,
        remaining_quantity=stock.quantity,  # Initially full
        unit_measure=stock.unit_measure.value,
        unit_cost=stock.unit_cost,
        total_cost=total_cost,
        provider_name=stock.provider_name,
        invoice_number=stock.invoice_number,
        location=stock.location,
        expiration_date=stock.expiration_date
    )
    
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    
    return new_batch


@router.get("/stock/{sku}", response_model=list[StockBatchResponse])
async def get_stock_by_sku(
    sku: str,
    include_allocated: bool = Query(False, description="Include fully allocated batches"),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los lotes de un SKU específico.
    
    Por defecto solo muestra lotes con stock disponible.
    """
    query = select(StockBatch).where(StockBatch.sku == sku.upper())
    
    if not include_allocated:
        query = query.where(StockBatch.remaining_quantity > 0)
    
    query = query.order_by(StockBatch.arrival_date.asc())
    
    batches = db.execute(query).scalars().all()
    
    if not batches:
        raise HTTPException(
            status_code=404,
            detail=f"No stock found for SKU: {sku}"
        )
    
    return batches


@router.get("/stock", response_model=list[StockBatchResponse])
async def list_stock(
    category: Optional[IngredientCategory] = None,
    location: Optional[str] = None,
    only_available: bool = Query(True, description="Only show batches with remaining quantity > 0"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Listar inventario con filtros opcionales.
    
    Soporta paginación y filtrado por categoría y ubicación.
    """
    query = select(StockBatch)
    
    # Apply filters
    if category:
        query = query.where(StockBatch.category == category.value)
    
    if location:
        query = query.where(StockBatch.location == location)
    
    if only_available:
        query = query.where(StockBatch.remaining_quantity > 0)
    
    # Order by arrival date (FIFO visualization)
    query = query.order_by(StockBatch.arrival_date.asc())
    
    # Pagination
    query = query.offset(skip).limit(limit)
    
    batches = db.execute(query).scalars().all()
    
    return batches


@router.post("/allocate", response_model=StockAllocationResponse)
async def allocate_stock(
    request: StockAllocationRequest,
    db: Session = Depends(get_db)
):
    """
    Asignar stock usando FIFO (First-In, First-Out).
    
    Este endpoint es crítico para producción: consume inventario
    automáticamente desde los lotes más antiguos.
    
    Returns trazabilidad completa de qué lotes fueron usados.
    """
    try:
        allocations = allocate_stock_fifo(
            sku=request.sku.upper(),
            amount_needed=request.amount_needed,
            session=db
        )
        
        # Commit transaction
        db.commit()
        
        # Calculate total allocated
        total_allocated = sum(
            Decimal(str(alloc["quantity"])) 
            for alloc in allocations
        )
        
        return StockAllocationResponse(
            sku=request.sku.upper(),
            total_allocated=total_allocated,
            allocations=allocations
        )
        
    except InsufficientStockError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_stock",
                "sku": e.sku,
                "requested": float(e.requested),
                "available": float(e.available),
                "message": str(e)
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/summary")
async def get_inventory_summary(db: Session = Depends(get_db)):
    """
    Resumen general del inventario por categoría.
    
    Útil para dashboards y reportes rápidos.
    """
    from sqlalchemy import func
    
    # Aggregate by category
    summary = db.query(
        StockBatch.category,
        func.count(StockBatch.id).label('total_batches'),
        func.sum(StockBatch.remaining_quantity).label('total_quantity'),
        func.sum(StockBatch.total_cost).label('total_value')
    ).filter(
        StockBatch.remaining_quantity > 0
    ).group_by(
        StockBatch.category
    ).all()
    
    return [
        {
            "category": row.category,
            "total_batches": row.total_batches,
            "total_quantity": float(row.total_quantity or 0),
            "total_value_mxn": float(row.total_value or 0)
        }
        for row in summary
    ]
