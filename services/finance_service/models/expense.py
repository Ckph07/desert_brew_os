"""
Expense Model — Tracks money paid out (proveedores, nóminas, compras, servicios).
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from database import Base
from datetime import datetime
import enum


class ExpenseType(str, enum.Enum):
    """Type of expense."""
    SUPPLIER_PAYMENT = "supplier_payment"   # Pago a proveedor de insumos
    PAYROLL = "payroll"                     # Nómina
    PURCHASE = "purchase"                   # Compra general
    UTILITY = "utility"                     # Servicios (luz, agua, gas, internet)
    RENT = "rent"                           # Renta
    TAX = "tax"                             # Impuestos
    MAINTENANCE = "maintenance"             # Mantenimiento de equipo
    OTHER = "other"


class ExpenseCategory(str, enum.Enum):
    """Budget category of expense."""
    RAW_MATERIALS = "raw_materials"     # Maltas, lúpulos, levaduras
    PACKAGING = "packaging"             # Barriles desechables, botellas, tapas
    PAYROLL = "payroll"                 # Nóminas y prestaciones
    ENERGY = "energy"                   # Electricidad
    WATER = "water"                     # Agua
    GAS = "gas"                         # Gas natural y CO₂
    RENT = "rent"                       # Renta de local/planta
    MAINTENANCE = "maintenance"         # Mantenimiento de equipos
    TRANSPORT = "transport"             # Transporte y desgaste vehicular
    MARKETING = "marketing"             # Publicidad y marketing
    COMMUNICATIONS = "communications"   # Teléfono, internet
    TAXES = "taxes"                     # IEPS, IVA, ISR
    OTHER = "other"


class Income_PaymentMethod(str, enum.Enum):
    """Payment method (shared with Income)."""
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    CHECK = "check"


class Expense(Base):
    """
    Expense record — money paid out by the business.

    Covers:
    - Supplier payments (linked via reference_id to PO or invoice)
    - Payroll (linked via reference_id to PayrollEntry)
    - Utility bills, rent, taxes, maintenance
    """
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Classification
    expense_type = Column(String(20), nullable=False, index=True)
    category = Column(String(20), nullable=False, index=True)

    # Reference to source document
    reference_id = Column(String(100), nullable=True, index=True)
    description = Column(String(500), nullable=False)

    # Amount
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)

    # Profit center
    profit_center = Column(String(20), nullable=False, index=True)  # factory, taproom, general

    # Supplier (optional)
    supplier_name = Column(String(200), nullable=True)

    # Who & when
    paid_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    paid_by = Column(String(100), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Expense(id={self.id}, type='{self.expense_type}', amount=${self.amount}, date={self.paid_date})>"
