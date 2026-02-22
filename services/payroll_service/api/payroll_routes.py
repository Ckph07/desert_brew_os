"""
FastAPI routes for Payroll Entries.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from models.employee import Employee, PayrollEntry
from schemas.payroll import (
    PayrollEntryCreate,
    PayrollEntryResponse,
)

router = APIRouter(prefix="/api/v1/payroll", tags=["Payroll Entries"])


@router.post("/entries", response_model=PayrollEntryResponse, status_code=201)
def create_payroll_entry(payload: PayrollEntryCreate, db: Session = Depends(get_db)):
    """
    Create a payroll entry for an employee.

    Auto-calculates:
    - base_salary = daily_salary × days_worked
    - overtime_amount = overtime_hours × overtime_rate
    - taxi_total = taxi_shifts × employee.taxi_allowance_per_shift
    - total_payment = base + overtime + tips_share + taxi + bonuses - deductions
    """
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {payload.employee_id} not found")

    daily_rate = float(employee.daily_salary)
    base_salary = round(daily_rate * payload.days_worked, 2)
    overtime_amount = round(payload.overtime_hours * payload.overtime_rate, 2)

    # Taxi calculation
    taxi_per_shift = float(employee.taxi_allowance_per_shift or 0)
    taxi_total = round(payload.taxi_shifts * taxi_per_shift, 2)

    total_payment = round(
        base_salary
        + overtime_amount
        + payload.tips_share
        + taxi_total
        + payload.bonuses
        - payload.deductions,
        2,
    )

    entry = PayrollEntry(
        employee_id=payload.employee_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        period_type=payload.period_type,
        days_worked=payload.days_worked,
        daily_rate=daily_rate,
        base_salary=base_salary,
        overtime_hours=payload.overtime_hours,
        overtime_rate=payload.overtime_rate,
        overtime_amount=overtime_amount,
        tips_share=payload.tips_share,
        tip_pool_id=payload.tip_pool_id,
        taxi_shifts=payload.taxi_shifts,
        taxi_total=taxi_total,
        bonuses=payload.bonuses,
        deductions=payload.deductions,
        deduction_notes=payload.deduction_notes,
        total_payment=total_payment,
        notes=payload.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/entries", response_model=list[PayrollEntryResponse])
def list_payroll_entries(
    employee_id: Optional[int] = Query(None),
    payment_status: Optional[str] = Query(None, description="PENDING or PAID"),
    department: Optional[str] = Query(None, description="Filter by employee department"),
    period_type: Optional[str] = Query(None, description="DAILY, WEEKLY, BIWEEKLY, MONTHLY"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List payroll entries with optional filters."""
    query = db.query(PayrollEntry)

    if employee_id:
        query = query.filter(PayrollEntry.employee_id == employee_id)
    if payment_status:
        query = query.filter(PayrollEntry.payment_status == payment_status.upper())
    if department:
        query = query.join(Employee).filter(Employee.department == department.upper())
    if period_type:
        query = query.filter(PayrollEntry.period_type == period_type.upper())

    return query.order_by(PayrollEntry.period_start.desc()).limit(limit).all()


@router.get("/entries/{entry_id}", response_model=PayrollEntryResponse)
def get_payroll_entry(entry_id: int, db: Session = Depends(get_db)):
    """Get payroll entry details."""
    entry = db.query(PayrollEntry).filter(PayrollEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"Payroll entry {entry_id} not found")
    return entry


@router.patch("/entries/{entry_id}/pay", response_model=PayrollEntryResponse)
def mark_as_paid(entry_id: int, db: Session = Depends(get_db)):
    """Mark a payroll entry as paid."""
    entry = db.query(PayrollEntry).filter(PayrollEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail=f"Payroll entry {entry_id} not found")
    if entry.payment_status == "PAID":
        raise HTTPException(status_code=400, detail="Entry is already paid")

    entry.payment_status = "PAID"
    entry.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)
    return entry
