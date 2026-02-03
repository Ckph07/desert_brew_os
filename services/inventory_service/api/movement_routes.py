"""
API routes for stock transfers and movement history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from datetime import date

from database import get_db
from models.transfer import StockTransfer
from models.movement import StockMovement
from models.enums import TransferStatus, MovementType
from schemas.movement import (
    StockTransferCreate,
    StockTransferResponse,
    StockMovementResponse,
)
from logic.stock_rotation import transfer_stock, InsufficientStockError

router = APIRouter()


@router.post("/transfer", response_model=StockTransferResponse, status_code=201)
async def create_transfer(
    transfer: StockTransferCreate,
    requested_by: Optional[str] = Query(None, description="Username"),
    db: Session = Depends(get_db)
):
    """
    Transfer stock from one location to another.
    
    Uses FIFO allocation from source, creates new batch at destination.
    Records full audit trail.
    """
    try:
        transfer_record = transfer_stock(
            sku=transfer.sku.upper(),
            quantity=transfer.quantity,
            from_location=transfer.from_location,
            to_location=transfer.to_location,
            requested_by=requested_by,
            notes=transfer.notes,
            session=db,
        )
        
        db.commit()
        db.refresh(transfer_record)
        
        return transfer_record
        
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
            detail=f"Transfer failed: {str(e)}"
        )


@router.get("/transfers", response_model=list[StockTransferResponse])
async def list_transfers(
    sku: Optional[str] = None,
    status: Optional[TransferStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List stock transfers with optional filters."""
    query = select(StockTransfer)
    
    if sku:
        query = query.where(StockTransfer.sku == sku.upper())
    
    if status:
        query = query.where(StockTransfer.status == status.value)
    
    query = query.order_by(StockTransfer.requested_at.desc())
    query = query.offset(skip).limit(limit)
    
    transfers = db.execute(query).scalars().all()
    return transfers


@router.get("/movements", response_model=list[StockMovementResponse])
async def list_movements(
    sku: Optional[str] = None,
    movement_type: Optional[MovementType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get movement history for audit/reporting.
    
    This is the audit trail - shows every stock change that happened.
    """
    query = select(StockMovement)
    
    if sku:
        query = query.where(StockMovement.sku == sku.upper())
    
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type.value)
    
    if start_date:
        query = query.where(StockMovement.created_at >= start_date)
    
    if end_date:
        query = query.where(StockMovement.created_at < end_date)
    
    query = query.order_by(StockMovement.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    movements = db.execute(query).scalars().all()
    return movements


@router.get("/movements/{sku}/summary")
async def get_movement_summary(
    sku: str,
    db: Session = Depends(get_db)
):
    """
    Get summary of movements by type for a SKU.
    
    Useful for understanding what happened to a product.
    """
    from sqlalchemy import func
    
    summary = db.query(
        StockMovement.movement_type,
        func.sum(StockMovement.quantity).label('total_quantity'),
        func.count(StockMovement.id).label('total_movements')
    ).filter(
        StockMovement.sku == sku.upper()
    ).group_by(
        StockMovement.movement_type
    ).all()
    
    return [
        {
            "movement_type": row.movement_type,
            "total_quantity": float(row.total_quantity or 0),
            "total_movements": row.total_movements
        }
        for row in summary
    ]
