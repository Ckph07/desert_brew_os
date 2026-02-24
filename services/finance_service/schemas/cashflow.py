"""
Pydantic schemas for Income, Expense, Balance, and Cashflow.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# =====================
# Income Schemas
# =====================

class IncomeCreate(BaseModel):
    """Create an income record."""
    income_type: str = Field(..., description="sales_note, cash_sale, b2b_invoice, other")
    category: str = Field(..., description="beer_sales, merch_sales, food_sales, event, other")
    reference_id: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., description="cash, card, transfer, check")
    profit_center: str = Field(..., description="taproom, distribution")
    received_date: Optional[datetime] = None
    received_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class IncomeUpdate(BaseModel):
    """Update an income record (partial)."""
    income_type: Optional[str] = None
    category: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    payment_method: Optional[str] = None
    profit_center: Optional[str] = None
    received_date: Optional[datetime] = None
    received_by: Optional[str] = None
    notes: Optional[str] = None


class IncomeResponse(BaseModel):
    """Income record response."""
    id: int
    income_type: str
    category: str
    reference_id: Optional[str]
    description: str
    amount: float
    payment_method: str
    profit_center: str
    received_date: datetime
    received_by: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class IncomeSummaryResponse(BaseModel):
    """Income summary for a period."""
    period_start: datetime
    period_end: datetime
    total_income: float
    count: int
    by_category: Dict[str, float]
    by_payment_method: Dict[str, float]
    by_profit_center: Dict[str, float]


# =====================
# Expense Schemas
# =====================

class ExpenseCreate(BaseModel):
    """Create an expense record."""
    expense_type: str = Field(..., description="supplier_payment, payroll, purchase, utility, rent, tax, maintenance, other")
    category: str = Field(..., description="raw_materials, packaging, payroll, energy, water, gas, rent, maintenance, transport, marketing, communications, taxes, other")
    reference_id: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., description="cash, card, transfer, check")
    profit_center: str = Field(..., description="factory, taproom, general")
    supplier_name: Optional[str] = Field(None, max_length=200)
    paid_date: Optional[datetime] = None
    paid_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    """Update an expense record (partial)."""
    expense_type: Optional[str] = None
    category: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    payment_method: Optional[str] = None
    profit_center: Optional[str] = None
    supplier_name: Optional[str] = None
    paid_date: Optional[datetime] = None
    paid_by: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    """Expense record response."""
    id: int
    expense_type: str
    category: str
    reference_id: Optional[str]
    description: str
    amount: float
    payment_method: str
    profit_center: str
    supplier_name: Optional[str]
    paid_date: datetime
    paid_by: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class ExpenseSummaryResponse(BaseModel):
    """Expense summary for a period."""
    period_start: datetime
    period_end: datetime
    total_expenses: float
    count: int
    by_category: Dict[str, float]
    by_type: Dict[str, float]
    by_profit_center: Dict[str, float]


# =====================
# Balance & Cashflow Schemas
# =====================

class BalanceSummaryResponse(BaseModel):
    """Consolidated balance — income vs expenses."""
    period_start: datetime
    period_end: datetime
    total_income: float
    total_expenses: float
    net_profit: float
    profit_margin_percentage: float
    income_by_category: Dict[str, float]
    expenses_by_category: Dict[str, float]
    income_by_profit_center: Dict[str, float]
    expenses_by_profit_center: Dict[str, float]


class CashflowMonthEntry(BaseModel):
    """One month of cashflow."""
    month: str       # "2026-02"
    income: float
    expenses: float
    net: float


class CashflowResponse(BaseModel):
    """Monthly cashflow report."""
    period_start: datetime
    period_end: datetime
    months: List[CashflowMonthEntry]
    total_income: float
    total_expenses: float
    total_net: float
