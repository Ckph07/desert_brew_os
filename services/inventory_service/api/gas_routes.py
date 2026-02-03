"""
API routes for gas tank management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from decimal import Decimal

from database import get_db
from models.gas_tank import GasTank, GasConsumption
from schemas.gas import (
    GasTankCreate,
    GasTankResponse,
    GasConsumptionCreate,
    GasConsumptionResponse
)

router = APIRouter()


@router.post("/gas-tanks", response_model=GasTankResponse, status_code=201)
async def register_gas_tank(
    tank: GasTankCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new gas tank in the system.
    
    Gas tanks are individual assets (not fungible).
    """
    # Check if tank_code already exists
    existing = db.execute(
        select(GasTank).where(GasTank.tank_code == tank.tank_code)
    ).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tank with code '{tank.tank_code}' already exists"
        )
    
    # Create new tank
    new_tank = GasTank(
        tank_code=tank.tank_code,
        sku=tank.sku.upper(),
        capacity_kg=tank.capacity_kg,
        capacity_m3=tank.capacity_m3,
        current_weight_kg=tank.capacity_kg,  # Start full
        current_volume_m3=tank.capacity_m3,
        is_full=True,
        is_empty=False,
        status="FULL",
        ownership_type=tank.ownership_type,
        supplier_id=tank.supplier_id,
        deposit_amount=tank.deposit_amount,
        location=tank.location,
    )
    
    db.add(new_tank)
    db.commit()
    db.refresh(new_tank)
    
    return new_tank


@router.get("/gas-tanks", response_model=list[GasTankResponse])
async def list_gas_tanks(
    sku: Optional[str] = None,
    status: Optional[str] = Query(None, description="FULL, IN_USE, EMPTY, MAINTENANCE"),
    location: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List gas tanks with optional filters.
    
    Useful for inventory management and reordering.
    """
    query = select(GasTank)
    
    if sku:
        query = query.where(GasTank.sku == sku.upper())
    
    if status:
        query = query.where(GasTank.status == status)
    
    if location:
        query = query.where(GasTank.location == location)
    
    query = query.order_by(GasTank.tank_code.asc())
    query = query.offset(skip).limit(limit)
    
    tanks = db.execute(query).scalars().all()
    return tanks


@router.get("/gas-tanks/{tank_code}", response_model=GasTankResponse)
async def get_gas_tank(
    tank_code: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific gas tank."""
    tank = db.execute(
        select(GasTank).where(GasTank.tank_code == tank_code)
    ).scalar_one_or_none()
    
    if not tank:
        raise HTTPException(
            status_code=404,
            detail=f"Tank '{tank_code}' not found"
        )
    
    return tank


@router.post("/gas-tanks/consume", response_model=GasConsumptionResponse, status_code=201)
async def consume_gas(
    consumption: GasConsumptionCreate,
    recorded_by: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Record gas consumption from a tank.
    
    Updates tank's current weight/volume.
    """
    # Find tank
    tank = db.execute(
        select(GasTank).where(GasTank.tank_code == consumption.tank_code)
    ).scalar_one_or_none()
    
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    # Validate consumption amount
    if consumption.quantity_kg:
        if not tank.current_weight_kg or consumption.quantity_kg > tank.current_weight_kg:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot consume {consumption.quantity_kg}kg. Only {tank.current_weight_kg}kg available."
            )
        # Update tank
        tank.current_weight_kg -= consumption.quantity_kg
    elif consumption.quantity_m3:
        if not tank.current_volume_m3 or consumption.quantity_m3 > tank.current_volume_m3:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot consume {consumption.quantity_m3}m³. Only {tank.current_volume_m3}m³ available."
            )
        # Update tank
        tank.current_volume_m3 -= consumption.quantity_m3
    else:
        raise HTTPException(
            status_code=400,
            detail="Must specify either quantity_kg or quantity_m3"
        )
    
    # Update tank status
    if tank.remaining_percentage < 10:
        tank.is_empty = True
        tank.is_full = False
        tank.status = "EMPTY"
    else:
        tank.is_full = False
        tank.status = "IN_USE"
    
    # Record consumption
    new_consumption = GasConsumption(
        tank_id=tank.id,
        quantity_consumed_kg=consumption.quantity_kg,
        quantity_consumed_m3=consumption.quantity_m3,
        production_batch_id=consumption.production_batch_id,
        purpose=consumption.purpose,
        notes=consumption.notes,
        recorded_by=recorded_by
    )
    
    db.add(new_consumption)
    db.commit()
    db.refresh(new_consumption)
    
    return new_consumption


@router.post("/gas-tanks/{tank_code}/refill")
async def refill_gas_tank(
    tank_code: str,
    db: Session = Depends(get_db)
):
    """
    Mark a gas tank as refilled (full).
    
    Used when a tank is refilled or replaced with a full one.
    """
    tank = db.execute(
        select(GasTank).where(GasTank.tank_code == tank_code)
    ).scalar_one_or_none()
    
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    # Reset to full
    tank.current_weight_kg = tank.capacity_kg
    tank.current_volume_m3 = tank.capacity_m3
    tank.is_full = True
    tank.is_empty = False
    tank.status = "FULL"
    
    db.commit()
    
    return {"message": f"Tank '{tank_code}' refilled successfully"}


@router.post("/gas-tanks/{tank_code}/return")
async def return_gas_tank(
    tank_code: str,
    db: Session = Depends(get_db)
):
    """
    Mark a gas tank as returned to supplier.
    
    Changes location and status.
    """
    tank = db.execute(
        select(GasTank).where(GasTank.tank_code == tank_code)
    ).scalar_one_or_none()
    
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    if tank.remaining_percentage > 10:
        raise HTTPException(
            status_code=400,
            detail=f"Tank must be nearly empty to return. Current: {tank.remaining_percentage:.1f}%"
        )
    
    tank.location = "With Supplier"
    tank.status = "EMPTY"
    
    db.commit()
    
    return {
        "message": f"Tank '{tank_code}' returned to supplier",
        "deposit_amount": float(tank.deposit_amount) if tank.deposit_amount else 0
    }


@router.get("/gas-tanks/{tank_code}/consumption-history", response_model=list[GasConsumptionResponse])
async def get_consumption_history(
    tank_code: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get consumption history for a specific tank."""
    tank = db.execute(
        select(GasTank).where(GasTank.tank_code == tank_code)
    ).scalar_one_or_none()
    
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    consumptions = db.execute(
        select(GasConsumption)
        .where(GasConsumption.tank_id == tank.id)
        .order_by(GasConsumption.consumed_at.desc())
        .limit(limit)
    ).scalars().all()
    
    return consumptions
