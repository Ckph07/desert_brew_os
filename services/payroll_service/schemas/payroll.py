"""
Pydantic schemas for Employee, Payroll, and TipPool CRUD.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


# === Employee Schemas ===

class EmployeeCreate(BaseModel):
    """Schema for creating an employee."""
    full_name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., max_length=50)
    department: str = Field(..., max_length=50)
    employment_type: str = Field("FIXED", pattern="^(FIXED|TEMPORARY)$")
    daily_salary: float = Field(..., gt=0)
    eligible_for_tips: bool = Field(False, description="True for taproom staff")
    taxi_allowance_per_shift: float = Field(0, ge=0, description="MXN per shift for transportation")
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    emergency_contact: Optional[str] = Field(None, max_length=200)
    hire_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Brewery fixed employee",
                    "value": {
                        "full_name": "Miguel Ángel Rodríguez",
                        "role": "BREWMASTER",
                        "department": "PRODUCTION",
                        "employment_type": "FIXED",
                        "daily_salary": 833.33,
                        "eligible_for_tips": False,
                    },
                },
                {
                    "summary": "Taproom fixed employee",
                    "value": {
                        "full_name": "Laura Martínez",
                        "role": "BARTENDER",
                        "department": "TAPROOM",
                        "employment_type": "FIXED",
                        "daily_salary": 500.00,
                        "eligible_for_tips": True,
                        "taxi_allowance_per_shift": 80.00,
                    },
                },
                {
                    "summary": "Taproom temp worker",
                    "value": {
                        "full_name": "Carlos Temp",
                        "role": "WAITER",
                        "department": "TAPROOM",
                        "employment_type": "TEMPORARY",
                        "daily_salary": 350.00,
                        "eligible_for_tips": True,
                        "taxi_allowance_per_shift": 80.00,
                    },
                },
            ]
        }


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=50)
    employment_type: Optional[str] = Field(None, pattern="^(FIXED|TEMPORARY)$")
    daily_salary: Optional[float] = Field(None, gt=0)
    eligible_for_tips: Optional[bool] = None
    taxi_allowance_per_shift: Optional[float] = Field(None, ge=0)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    emergency_contact: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class EmployeeResponse(BaseModel):
    """Employee response."""
    id: int
    employee_code: str
    full_name: str
    role: str
    department: str
    employment_type: str
    daily_salary: float
    monthly_salary: Optional[float] = None
    eligible_for_tips: bool
    taxi_allowance_per_shift: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = None
    hire_date: datetime
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Payroll Schemas ===

class PayrollEntryCreate(BaseModel):
    """Schema for creating a payroll entry."""
    employee_id: int
    period_start: datetime
    period_end: datetime
    period_type: str = Field("WEEKLY", pattern="^(DAILY|WEEKLY|BIWEEKLY|MONTHLY)$")
    days_worked: int = Field(..., ge=0, le=31)
    overtime_hours: float = Field(0, ge=0)
    overtime_rate: float = Field(0, ge=0)
    # Taproom extras
    tips_share: float = Field(0, ge=0, description="Share from tip pool")
    tip_pool_id: Optional[int] = None
    taxi_shifts: int = Field(0, ge=0, description="Number of shifts with taxi support")
    bonuses: float = Field(0, ge=0)
    deductions: float = Field(0, ge=0)
    deduction_notes: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=500)


class PayrollEntryResponse(BaseModel):
    """Payroll entry response."""
    id: int
    employee_id: int
    period_start: datetime
    period_end: datetime
    period_type: str
    days_worked: int
    daily_rate: float
    base_salary: float
    overtime_hours: float
    overtime_rate: float
    overtime_amount: float
    tips_share: float
    tip_pool_id: Optional[int] = None
    taxi_shifts: int
    taxi_total: float
    bonuses: float
    deductions: float
    deduction_notes: Optional[str] = None
    total_payment: float
    payment_status: str
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === TipPool Schemas ===

class TipPoolCreate(BaseModel):
    """Schema for creating a weekly tip pool distribution."""
    week_start: date = Field(..., description="Sunday of the week")
    week_end: date = Field(..., description="Saturday of the week")
    total_collected: float = Field(..., gt=0, description="Total tips collected Sun-Sat")
    participant_ids: list[int] = Field(..., min_length=1, description="Employee IDs participating")
    notes: Optional[str] = Field(None, max_length=500)
    created_by: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "week_start": "2026-02-15",
                "week_end": "2026-02-21",
                "total_collected": 4500.00,
                "participant_ids": [4, 5, 6, 7],
                "notes": "Good week, Valentine's event",
                "created_by": "admin",
            }
        }


class TipPoolResponse(BaseModel):
    """Tip pool distribution response."""
    id: int
    week_start: date
    week_end: date
    total_collected: float
    num_participants: int
    per_person_share: float
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TipPoolDetailResponse(TipPoolResponse):
    """Tip pool with participant details."""
    participants: list[dict] = []
    # [{"employee_id": 4, "name": "Laura", "share": 1125.00}, ...]
