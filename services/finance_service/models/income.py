"""
Income Model — Tracks revenue received (notas pagadas, ventas en efectivo, B2B).
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from database import Base
from datetime import datetime
import enum


class IncomeType(str, enum.Enum):
    """Source of income."""
    SALES_NOTE = "sales_note"       # Nota de venta pagada (Sales Service)
    CASH_SALE = "cash_sale"         # Venta directa en efectivo
    B2B_INVOICE = "b2b_invoice"     # Factura B2B (distribución)
    OTHER = "other"


class IncomeCategory(str, enum.Enum):
    """Category of revenue."""
    BEER_SALES = "beer_sales"       # Venta de cerveza (propia, comercial, invitada)
    MERCH_SALES = "merch_sales"     # Venta de merchandise
    FOOD_SALES = "food_sales"       # Venta de alimentos
    EVENT = "event"                 # Eventos privados / renta de espacio
    OTHER = "other"


class PaymentMethod(str, enum.Enum):
    """Payment method."""
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    CHECK = "check"


class Income(Base):
    """
    Income record — money received by the business.

    Links to Sales Service via reference_id (nota de venta ID).
    """
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Classification
    income_type = Column(String(20), nullable=False, index=True)
    category = Column(String(20), nullable=False, index=True)

    # Reference to source document
    reference_id = Column(String(100), nullable=True, index=True)
    description = Column(String(500), nullable=False)

    # Amount
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)

    # Profit center
    profit_center = Column(String(20), nullable=False, index=True)

    # Who & when
    received_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    received_by = Column(String(100), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Income(id={self.id}, type='{self.income_type}', amount=${self.amount}, date={self.received_date})>"
