"""
Expense API routes — CRUD + summary.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models.expense import Expense
from schemas.cashflow import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSummaryResponse
)

router = APIRouter(prefix="/api/v1/finance", tags=["Expenses"])


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    """Register an expense (pago a proveedor, nómina, compra, servicio, etc.)."""
    expense = Expense(
        expense_type=payload.expense_type,
        category=payload.category,
        reference_id=payload.reference_id,
        description=payload.description,
        amount=payload.amount,
        payment_method=payload.payment_method,
        profit_center=payload.profit_center,
        supplier_name=payload.supplier_name,
        paid_date=payload.paid_date or datetime.utcnow(),
        paid_by=payload.paid_by,
        notes=payload.notes,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/expenses", response_model=List[ExpenseResponse])
def list_expenses(
    expense_type: str = Query(None),
    category: str = Query(None),
    profit_center: str = Query(None),
    supplier_name: str = Query(None),
    payment_method: str = Query(None),
    days: int = Query(None, ge=1, le=365, description="Filter last N days"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List expenses with filters."""
    query = db.query(Expense)

    if expense_type:
        query = query.filter(Expense.expense_type == expense_type)
    if category:
        query = query.filter(Expense.category == category)
    if profit_center:
        query = query.filter(Expense.profit_center == profit_center)
    if supplier_name:
        query = query.filter(Expense.supplier_name.ilike(f"%{supplier_name}%"))
    if payment_method:
        query = query.filter(Expense.payment_method == payment_method)
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Expense.paid_date >= cutoff)

    return query.order_by(Expense.paid_date.desc()).offset(skip).limit(limit).all()


@router.get("/expenses/summary", response_model=ExpenseSummaryResponse)
def expense_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get expense summary grouped by category, type, and profit center."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    expenses = db.query(Expense).filter(Expense.paid_date >= cutoff).all()

    by_category: dict = {}
    by_type: dict = {}
    by_pc: dict = {}
    total = 0.0

    for e in expenses:
        amt = float(e.amount)
        total += amt
        by_category[e.category] = by_category.get(e.category, 0) + amt
        by_type[e.expense_type] = by_type.get(e.expense_type, 0) + amt
        by_pc[e.profit_center] = by_pc.get(e.profit_center, 0) + amt

    return ExpenseSummaryResponse(
        period_start=cutoff,
        period_end=datetime.utcnow(),
        total_expenses=round(total, 2),
        count=len(expenses),
        by_category={k: round(v, 2) for k, v in by_category.items()},
        by_type={k: round(v, 2) for k, v in by_type.items()},
        by_profit_center={k: round(v, 2) for k, v in by_pc.items()},
    )


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """Get expense detail."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(404, f"Expense {expense_id} not found")
    return expense


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db)):
    """Update an expense record."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(404, f"Expense {expense_id} not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(expense, key, value)

    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Delete an expense record."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(404, f"Expense {expense_id} not found")
    db.delete(expense)
    db.commit()
