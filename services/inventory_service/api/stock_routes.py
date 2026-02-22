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


@router.patch("/stock-batches/{batch_id}/consume")
async def consume_stock_batch(
    batch_id: int,
    quantity: float = Query(..., gt=0, description="Quantity to consume"),
    unit: str = Query(..., description="Unit of measure"),
    reason: Optional[str] = Query(None, description="Reason for consumption"),
    db: Session = Depends(get_db)
):
    """
    Consume quantity from a specific StockBatch.
    
    Used by Production Service when allocating ingredients to batches.
    Uses pessimistic locking to prevent race conditions.
    
    Args:
        batch_id: ID of the StockBatch
        quantity: Amount to consume
        unit: Unit of measure (must match StockBatch unit)
        reason: Optional reason (e.g., "Production Batch #IPA-001")
    
    Returns:
        Updated StockBatch with new remaining_quantity
    """
    # Use pessimistic locking to prevent concurrent consumption
    stock_batch = db.execute(
        select(StockBatch)
        .where(StockBatch.id == batch_id)
        .with_for_update()
    ).scalar_one_or_none()
    
    if not stock_batch:
        raise HTTPException(404, f"Stock batch {batch_id} not found")
    
    # Validate unit matches
    if unit.upper() != stock_batch.unit_measure.upper():
        raise HTTPException(
            400,
            f"Unit mismatch: StockBatch uses {stock_batch.unit_measure}, requested {unit}"
        )
    
    # Check sufficient quantity
    if stock_batch.remaining_quantity < quantity:
        raise HTTPException(
            400,
            {
                "error": "insufficient_quantity",
                "batch_id": batch_id,
                "requested": quantity,
                "available": float(stock_batch.remaining_quantity),
                "message": f"Insufficient quantity in batch {batch_id}: "
                          f"requested {quantity}, available {stock_batch.remaining_quantity}"
            }
        )
    
    # Consume quantity
    old_quantity = stock_batch.remaining_quantity
    stock_batch.remaining_quantity -= Decimal(str(quantity))
    
    # Create movement record (if StockMovement model exists)
    # TODO: Add StockMovement tracking in future sprint
    
    db.commit()
    db.refresh(stock_batch)
    
    return {
        "status": "consumed",
        "batch_id": batch_id,
        "batch_number": stock_batch.batch_number,
        "quantity_consumed": quantity,
        "unit": unit,
        "previous_quantity": float(old_quantity),
        "remaining_quantity": float(stock_batch.remaining_quantity),
        "reason": reason
    }


@router.get("/stock-batches")
async def get_stock_batches(
    ingredient_name: Optional[str] = Query(None, description="Filter by ingredient/SKU name"),
    available_only: bool = Query(False, description="Only show batches with remaining quantity > 0"),
    min_quantity: float = Query(0.0, description="Minimum remaining quantity"),
    sort: str = Query("created_at_asc", description="Sort order: created_at_asc (FIFO) or created_at_desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get StockBatches with filters (for Production Service FIFO queries).
    
    Args:
        ingredient_name: Filter by SKU or ingredient name (partial match)
        available_only: Only return batches with remaining_quantity > 0
        min_quantity: Minimum remaining quantity threshold
        sort: Sort order (created_at_asc for FIFO, created_at_desc for LIFO)
    
    Returns:
        List of StockBatches matching criteria
    """
    query = select(StockBatch)
    
    # Filter by ingredient name (partial match on SKU)
    if ingredient_name:
        query = query.where(StockBatch.sku.ilike(f"%{ingredient_name}%"))
    
    # Filter available only
    if available_only:
        query = query.where(StockBatch.remaining_quantity > min_quantity)
    
    # Sort order (FIFO = oldest first)
    if sort == "created_at_asc":
        query = query.order_by(StockBatch.arrival_date.asc())
    else:
        query = query.order_by(StockBatch.arrival_date.desc())
    
    # Pagination
    query = query.offset(skip).limit(limit)
    
    batches = db.execute(query).scalars().all()
    
    return [
        {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "sku": batch.sku,
            "category": batch.category,
            "available_quantity": float(batch.remaining_quantity),
            "unit_cost": float(batch.unit_cost),
            "unit_measure": batch.unit_measure,
            "supplier_name": batch.provider_name,
            "arrival_date": batch.arrival_date.isoformat() if batch.arrival_date else None
        }
        for batch in batches
    ]
