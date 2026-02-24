"""
Income API routes — CRUD + summary.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models.income import Income
from schemas.cashflow import (
    IncomeCreate, IncomeUpdate, IncomeResponse, IncomeSummaryResponse
)

router = APIRouter(prefix="/api/v1/finance", tags=["Income"])


@router.post("/incomes", response_model=IncomeResponse, status_code=201)
def create_income(payload: IncomeCreate, db: Session = Depends(get_db)):
    """Register an income (nota pagada, venta en efectivo, etc.)."""
    income = Income(
        income_type=payload.income_type,
        category=payload.category,
        reference_id=payload.reference_id,
        description=payload.description,
        amount=payload.amount,
        payment_method=payload.payment_method,
        profit_center=payload.profit_center,
        received_date=payload.received_date or datetime.utcnow(),
        received_by=payload.received_by,
        notes=payload.notes,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


@router.get("/incomes", response_model=List[IncomeResponse])
def list_incomes(
    income_type: str = Query(None),
    category: str = Query(None),
    profit_center: str = Query(None),
    payment_method: str = Query(None),
    days: int = Query(None, ge=1, le=365, description="Filter last N days"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List incomes with filters."""
    query = db.query(Income)

    if income_type:
        query = query.filter(Income.income_type == income_type)
    if category:
        query = query.filter(Income.category == category)
    if profit_center:
        query = query.filter(Income.profit_center == profit_center)
    if payment_method:
        query = query.filter(Income.payment_method == payment_method)
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Income.received_date >= cutoff)

    return query.order_by(Income.received_date.desc()).offset(skip).limit(limit).all()


@router.get("/incomes/summary", response_model=IncomeSummaryResponse)
def income_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get income summary grouped by category, payment method, and profit center."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    incomes = db.query(Income).filter(Income.received_date >= cutoff).all()

    by_category: dict = {}
    by_method: dict = {}
    by_pc: dict = {}
    total = 0.0

    for i in incomes:
        amt = float(i.amount)
        total += amt
        by_category[i.category] = by_category.get(i.category, 0) + amt
        by_method[i.payment_method] = by_method.get(i.payment_method, 0) + amt
        by_pc[i.profit_center] = by_pc.get(i.profit_center, 0) + amt

    return IncomeSummaryResponse(
        period_start=cutoff,
        period_end=datetime.utcnow(),
        total_income=round(total, 2),
        count=len(incomes),
        by_category={k: round(v, 2) for k, v in by_category.items()},
        by_payment_method={k: round(v, 2) for k, v in by_method.items()},
        by_profit_center={k: round(v, 2) for k, v in by_pc.items()},
    )


@router.get("/incomes/{income_id}", response_model=IncomeResponse)
def get_income(income_id: int, db: Session = Depends(get_db)):
    """Get income detail."""
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        raise HTTPException(404, f"Income {income_id} not found")
    return income


@router.patch("/incomes/{income_id}", response_model=IncomeResponse)
def update_income(income_id: int, payload: IncomeUpdate, db: Session = Depends(get_db)):
    """Update an income record."""
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        raise HTTPException(404, f"Income {income_id} not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(income, key, value)

    db.commit()
    db.refresh(income)
    return income


@router.delete("/incomes/{income_id}", status_code=204)
def delete_income(income_id: int, db: Session = Depends(get_db)):
    """Delete an income record."""
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        raise HTTPException(404, f"Income {income_id} not found")
    db.delete(income)
    db.commit()
