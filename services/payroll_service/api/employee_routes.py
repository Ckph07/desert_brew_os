"""
FastAPI routes for Employee CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from models.employee import Employee
from schemas.payroll import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

router = APIRouter(prefix="/api/v1/payroll", tags=["Employees"])


def _generate_employee_code(db: Session) -> str:
    """Auto-generate employee code like EMP-001."""
    last = db.query(Employee).order_by(Employee.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"EMP-{next_num:03d}"


@router.post("/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    """
    Create a new employee.

    For TAPROOM department, set eligible_for_tips=True and taxi_allowance_per_shift.
    For TEMPORARY employees, monthly_salary is not calculated.
    """
    monthly = round(payload.daily_salary * 30, 2) if payload.employment_type == "FIXED" else None

    employee = Employee(
        employee_code=_generate_employee_code(db),
        full_name=payload.full_name,
        role=payload.role.upper(),
        department=payload.department.upper(),
        employment_type=payload.employment_type.upper(),
        daily_salary=payload.daily_salary,
        monthly_salary=monthly,
        eligible_for_tips=payload.eligible_for_tips,
        taxi_allowance_per_shift=payload.taxi_allowance_per_shift,
        phone=payload.phone,
        email=payload.email,
        emergency_contact=payload.emergency_contact,
        hire_date=payload.hire_date or datetime.utcnow(),
        notes=payload.notes,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/employees", response_model=list[EmployeeResponse])
def list_employees(
    department: Optional[str] = Query(None, description="PRODUCTION, TAPROOM, LOGISTICS, ADMIN"),
    role: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None, description="FIXED or TEMPORARY"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List employees with optional filters."""
    query = db.query(Employee)

    if active_only:
        query = query.filter(Employee.is_active == True)
    if department:
        query = query.filter(Employee.department == department.upper())
    if role:
        query = query.filter(Employee.role == role.upper())
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type.upper())

    return query.order_by(Employee.department.asc(), Employee.full_name.asc()).all()


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get employee details."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return employee


@router.patch("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    """Update an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Recalculate monthly if daily changes (fixed only)
    if "daily_salary" in update_data:
        emp_type = update_data.get("employment_type", employee.employment_type)
        if emp_type == "FIXED":
            update_data["monthly_salary"] = round(update_data["daily_salary"] * 30, 2)
        else:
            update_data["monthly_salary"] = None

    for key, value in update_data.items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)
    return employee
