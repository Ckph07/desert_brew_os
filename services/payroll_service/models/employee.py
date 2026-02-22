"""
Employee and Payroll Models - Department-specific payroll tracking.

Business Context:
- Cervecería (Brewery): 3 fixed employees, standard weekly payroll
- Taproom: 3 fixed employees + temps (daily pay), weekly tip pool (Sun-Sat),
  taxi support allowance, staff rotation

Payroll calculation:
- Fixed: daily_salary × days_worked
- Temp: daily_salary × days_worked (no benefits)
- Tips: total_tips_week / num_participating_members
- Taxi: flat amount per shift (Taproom only)
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Index, Date
from database import Base
from datetime import datetime, date
from decimal import Decimal


class Employee(Base):
    """
    Employee model supporting both fixed and temporary staff.

    Business Rules:
    - Brewery: 3 fixed employees (PRODUCTION department)
    - Taproom: 3 fixed + rotating temps (TAPROOM department)
    - employment_type: "FIXED" or "TEMPORARY" (daily pay, no benefits)
    - monthly_salary = daily_salary × 30 (auto-calculated, fixed only)
    - Taproom staff eligible for tip pool + taxi support
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_code = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False, index=True)

    # Role & Department
    role = Column(String(50), nullable=False)
    # Brewery: "BREWMASTER", "ASSISTANT_BREWER", "PACKAGING_OPERATOR"
    # Taproom: "TAPROOM_MANAGER", "BARTENDER", "WAITER", "HOST"
    # Logistics: "DELIVERY_DRIVER"
    # Admin: "ADMIN", "ACCOUNTANT"
    department = Column(String(50), nullable=False)
    # "PRODUCTION" (Cervecería), "TAPROOM", "LOGISTICS", "ADMIN"

    # Employment type
    employment_type = Column(String(20), nullable=False, default="FIXED")
    # "FIXED" = Planta (weekly/biweekly payroll, benefits)
    # "TEMPORARY" = Temporal (daily pay, no benefits, rotation)

    # Salary
    daily_salary = Column(Numeric(10, 2), nullable=False)
    monthly_salary = Column(Numeric(10, 2), nullable=True)  # daily × 30 (fixed only)

    # Taproom-specific
    eligible_for_tips = Column(Boolean, nullable=False, default=False)
    # True for all taproom staff (fixed + temp)
    taxi_allowance_per_shift = Column(Numeric(8, 2), nullable=True, default=0)
    # Flat amount per shift for transportation

    # Contact
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    emergency_contact = Column(String(200), nullable=True)

    # Employment
    hire_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    notes = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_employee_dept_role', 'department', 'role'),
        Index('idx_employee_dept_type', 'department', 'employment_type'),
    )

    def __repr__(self):
        return f"<Employee(code='{self.employee_code}', name='{self.full_name}', dept='{self.department}', type='{self.employment_type}')>"


class PayrollEntry(Base):
    """
    Payroll entry for a specific period.

    Calculates: base_salary = daily_salary × days_worked
    total_payment = base + overtime + tips_share + taxi + bonuses - deductions
    """
    __tablename__ = "payroll_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False, default="WEEKLY")
    # "DAILY" (temps), "WEEKLY", "BIWEEKLY", "MONTHLY"

    # Base calculation
    days_worked = Column(Integer, nullable=False)
    daily_rate = Column(Numeric(10, 2), nullable=False)  # Snapshot of daily_salary
    base_salary = Column(Numeric(10, 2), nullable=False)  # daily_rate × days_worked

    # Extras
    overtime_hours = Column(Numeric(5, 2), nullable=False, default=0)
    overtime_rate = Column(Numeric(10, 2), nullable=False, default=0)
    overtime_amount = Column(Numeric(10, 2), nullable=False, default=0)

    # Taproom-specific
    tips_share = Column(Numeric(10, 2), nullable=False, default=0)
    # Employee's share from the weekly tip pool
    tip_pool_id = Column(Integer, ForeignKey("tip_pools.id"), nullable=True)
    # Link to the TipPool distribution

    taxi_shifts = Column(Integer, nullable=False, default=0)
    # Number of shifts that get taxi allowance
    taxi_total = Column(Numeric(8, 2), nullable=False, default=0)
    # taxi_shifts × taxi_allowance_per_shift

    bonuses = Column(Numeric(10, 2), nullable=False, default=0)

    # Deductions
    deductions = Column(Numeric(10, 2), nullable=False, default=0)
    deduction_notes = Column(String(200), nullable=True)

    # Total
    total_payment = Column(Numeric(12, 2), nullable=False)
    # = base_salary + overtime + tips_share + taxi_total + bonuses - deductions

    # Status
    payment_status = Column(String(20), nullable=False, default="PENDING")
    # "PENDING", "PAID"
    paid_at = Column(DateTime, nullable=True)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_payroll_employee_period', 'employee_id', 'period_start'),
        Index('idx_payroll_status', 'payment_status'),
    )

    def __repr__(self):
        return f"<PayrollEntry(emp={self.employee_id}, period={self.period_start}-{self.period_end}, total=${self.total_payment})>"

    def calculate_total(self) -> None:
        """Calculate total payment from all components."""
        self.total_payment = (
            Decimal(str(self.base_salary))
            + Decimal(str(self.overtime_amount))
            + Decimal(str(self.tips_share))
            + Decimal(str(self.taxi_total))
            + Decimal(str(self.bonuses))
            - Decimal(str(self.deductions))
        )


class TipPool(Base):
    """
    Weekly tip pool distribution for Taproom.

    Business Rules:
    - Tips collected Sunday to Saturday (complete week)
    - Total tips divided equally among all participating members
    - Both fixed and temp taproom staff participate
    - per_person = total_collected / num_participants
    """
    __tablename__ = "tip_pools"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Period (Sun-Sat)
    week_start = Column(Date, nullable=False, index=True)  # Sunday
    week_end = Column(Date, nullable=False)                 # Saturday

    # Amounts
    total_collected = Column(Numeric(12, 2), nullable=False)
    num_participants = Column(Integer, nullable=False)
    per_person_share = Column(Numeric(10, 2), nullable=False)
    # = total_collected / num_participants

    # Metadata
    notes = Column(String(500), nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_tip_pool_week', 'week_start'),
    )

    def __repr__(self):
        return f"<TipPool(week={self.week_start}, total=${self.total_collected}, per_person=${self.per_person_share})>"
