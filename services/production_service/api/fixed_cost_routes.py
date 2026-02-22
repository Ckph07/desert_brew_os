"""
FastAPI routes for Fixed Monthly Costs and Production Target CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from decimal import Decimal

from database import get_db
from models.fixed_monthly_cost import FixedMonthlyCost, ProductionTarget
from schemas.cost_management import (
    FixedMonthlyCostCreate,
    FixedMonthlyCostUpdate,
    FixedMonthlyCostResponse,
    ProductionTargetCreate,
    ProductionTargetResponse,
    CostSummaryResponse,
)

router = APIRouter(prefix="/api/v1/production/costs", tags=["Fixed Costs"])


# === Fixed Monthly Costs ===

@router.post("/fixed", response_model=FixedMonthlyCostResponse, status_code=201)
def create_fixed_cost(payload: FixedMonthlyCostCreate, db: Session = Depends(get_db)):
    """Create a fixed monthly cost line item."""
    cost = FixedMonthlyCost(
        category=payload.category.upper(),
        concept=payload.concept,
        monthly_amount=payload.monthly_amount,
        notes=payload.notes,
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return cost


@router.get("/fixed", response_model=list[FixedMonthlyCostResponse])
def list_fixed_costs(
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List fixed monthly costs."""
    query = db.query(FixedMonthlyCost)

    if active_only:
        query = query.filter(FixedMonthlyCost.is_active == True)
    if category:
        query = query.filter(FixedMonthlyCost.category == category.upper())

    return query.order_by(FixedMonthlyCost.category.asc()).all()


@router.patch("/fixed/{cost_id}", response_model=FixedMonthlyCostResponse)
def update_fixed_cost(
    cost_id: int,
    payload: FixedMonthlyCostUpdate,
    db: Session = Depends(get_db),
):
    """Update a fixed cost line item."""
    cost = db.query(FixedMonthlyCost).filter(FixedMonthlyCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail=f"Fixed cost {cost_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cost, key, value)

    db.commit()
    db.refresh(cost)
    return cost


@router.delete("/fixed/{cost_id}", status_code=204)
def delete_fixed_cost(cost_id: int, db: Session = Depends(get_db)):
    """Soft-delete a fixed cost (sets is_active=False)."""
    cost = db.query(FixedMonthlyCost).filter(FixedMonthlyCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail=f"Fixed cost {cost_id} not found")

    cost.is_active = False
    db.commit()


# === Production Target ===

@router.post("/target", response_model=ProductionTargetResponse, status_code=201)
def set_production_target(payload: ProductionTargetCreate, db: Session = Depends(get_db)):
    """
    Set a production target for a period.

    Automatically calculates fixed_cost_per_liter from active fixed costs.
    Sets this target as current (deactivates previous current target).
    """
    # Calculate total fixed costs
    total_fixed = db.query(
        func.coalesce(func.sum(FixedMonthlyCost.monthly_amount), 0)
    ).filter(FixedMonthlyCost.is_active == True).scalar()

    total_fixed = float(total_fixed)
    cost_per_liter = round(total_fixed / payload.target_liters_monthly, 2) if payload.target_liters_monthly > 0 else 0

    # Deactivate previous current target
    db.query(ProductionTarget).filter(ProductionTarget.is_current == True).update(
        {"is_current": False}
    )

    target = ProductionTarget(
        period=payload.period,
        target_liters_monthly=payload.target_liters_monthly,
        total_fixed_cost=total_fixed,
        fixed_cost_per_liter=cost_per_liter,
        is_current=True,
        notes=payload.notes,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.get("/target", response_model=ProductionTargetResponse)
def get_current_target(db: Session = Depends(get_db)):
    """Get the current production target with per-liter cost."""
    target = db.query(ProductionTarget).filter(ProductionTarget.is_current == True).first()
    if not target:
        raise HTTPException(status_code=404, detail="No production target set. POST /costs/target first.")
    return target


# === Summary ===

@router.get("/summary", response_model=CostSummaryResponse)
def get_cost_summary(db: Session = Depends(get_db)):
    """
    Get consolidated cost summary.

    Returns total fixed costs, per-liter breakdown, and ingredient count.
    """
    # Fixed costs by category
    fixed_results = db.query(
        FixedMonthlyCost.category,
        func.sum(FixedMonthlyCost.monthly_amount).label("total"),
    ).filter(
        FixedMonthlyCost.is_active == True,
    ).group_by(FixedMonthlyCost.category).all()

    total_fixed = sum(float(r.total) for r in fixed_results)

    # Current target
    target = db.query(ProductionTarget).filter(ProductionTarget.is_current == True).first()
    target_liters = float(target.target_liters_monthly) if target else 1800.0

    cost_per_liter = round(total_fixed / target_liters, 2) if target_liters > 0 else 0

    # Ingredient count
    from models.ingredient_price import IngredientPrice
    ingredient_count = db.query(func.count(IngredientPrice.id)).filter(
        IngredientPrice.is_active == True
    ).scalar()

    return CostSummaryResponse(
        total_fixed_monthly=total_fixed,
        target_liters=target_liters,
        fixed_cost_per_liter=cost_per_liter,
        cost_breakdown=[
            {"category": r.category, "monthly_amount": float(r.total)}
            for r in fixed_results
        ],
        ingredient_count=ingredient_count or 0,
    )
