"""
Sales Note Models - Invoice/Note management.

Purpose: Track sales notes (notas de venta) with line items.
Tax calculation (IEPS/IVA) is togglable since not all sales are invoiced.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Index
from database import Base
from datetime import datetime
from decimal import Decimal


class SalesNote(Base):
    """
    Nota de venta (sales note / order).

    Business Rules:
    - note_number is auto-generated: 8-digit zero-padded (00000001)
    - include_taxes: When False, IEPS/IVA fields remain at 0 (not invoiced)
    - Only DRAFT notes can be modified
    - CONFIRMED notes are immutable
    - Totals are recalculated from items
    """
    __tablename__ = "sales_notes"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identification
    note_number = Column(String(30), unique=True, nullable=False, index=True)

    # Client reference
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    client_name = Column(String(200), nullable=True)  # Denormalized for PDF

    # Issuer info (Desert Brew Co.)
    issuer_name = Column(String(200), nullable=False, default="César Krisabd Padilla Hernández")
    issuer_rfc = Column(String(20), nullable=False, default="PAHC980207LA1")
    issuer_address = Column(String(300), nullable=False, default="SERPENTIS 178")
    issuer_phone = Column(String(50), nullable=False, default="8443823737")

    # === TAX TOGGLE ===
    include_taxes = Column(Boolean, nullable=False, default=False)
    # When False: IEPS and IVA shown as empty/0 in PDF (not invoiced)
    # When True: IEPS and IVA calculated and shown

    # Totals (auto-calculated from items)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    ieps_total = Column(Numeric(12, 2), nullable=False, default=0)
    iva_total = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    total_liters = Column(Numeric(10, 2), nullable=False, default=0)  # Total liters for beer items

    # Metadata
    channel = Column(String(20), nullable=False, default="B2B")  # "TAPROOM", "B2B", "ECOMMERCE"
    payment_method = Column(String(30), nullable=False, default="TRANSFERENCIA")
    # "EFECTIVO", "TARJETA", "TRANSFERENCIA", "CREDITO"
    payment_status = Column(String(20), nullable=False, default="PENDING")
    # "PENDING", "PAID", "PARTIAL"
    status = Column(String(20), nullable=False, default="DRAFT")
    # "DRAFT", "CONFIRMED", "CANCELLED"

    notes = Column(String(500), nullable=True)
    created_by = Column(String(100), nullable=True)

    # Timestamps
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_note_client_date', 'client_id', 'created_at'),
        Index('idx_note_status', 'status'),
    )

    def __repr__(self):
        return f"<SalesNote(number='{self.note_number}', client='{self.client_name}', total=${self.total})>"

    def recalculate_totals(self, items: list) -> None:
        """
        Recalculate note totals from items.

        Only calculates taxes if include_taxes is True.
        """
        subtotal = Decimal('0.00')
        ieps = Decimal('0.00')
        iva = Decimal('0.00')
        liters = Decimal('0.00')

        for item in items:
            subtotal += Decimal(str(item.subtotal))
            if self.include_taxes:
                ieps += Decimal(str(item.ieps_amount or 0))
                iva += Decimal(str(item.iva_amount or 0))
            if item.unit_measure and item.unit_measure.upper() in ("LITROS", "L"):
                liters += Decimal(str(item.quantity))

        self.subtotal = subtotal
        self.ieps_total = ieps if self.include_taxes else Decimal('0.00')
        self.iva_total = iva if self.include_taxes else Decimal('0.00')
        self.total = subtotal + self.ieps_total + self.iva_total
        self.total_liters = liters
        self.updated_at = datetime.utcnow()


class SalesNoteItem(Base):
    """
    Line item in a sales note.

    Denormalizes product info for PDF rendering (snapshot at time of sale).
    """
    __tablename__ = "sales_note_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_note_id = Column(Integer, ForeignKey("sales_notes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Product reference (denormalized snapshot)
    product_id = Column(Integer, ForeignKey("product_catalog.id"), nullable=True)
    sku = Column(String(100), nullable=True)
    product_name = Column(String(200), nullable=False)
    unit_measure = Column(String(20), nullable=False, default="LITROS")  # "LITROS", "UNITS", "KEGS"

    # Quantity and pricing
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_pct = Column(Numeric(5, 2), nullable=False, default=0)

    # Calculated fields
    subtotal = Column(Numeric(12, 2), nullable=False)  # qty × unit_price × (1 - discount)
    ieps_amount = Column(Numeric(10, 2), nullable=False, default=0)
    iva_amount = Column(Numeric(10, 2), nullable=False, default=0)
    line_total = Column(Numeric(12, 2), nullable=False)  # subtotal + ieps + iva

    def __repr__(self):
        return f"<SalesNoteItem(qty={self.quantity} {self.unit_measure} '{self.product_name}' ${self.line_total})>"

    def calculate_totals(self, include_taxes: bool = False, ieps_rate: float = 0, iva_rate: float = 0.16) -> None:
        """Calculate line item totals."""
        qty = Decimal(str(self.quantity))
        price = Decimal(str(self.unit_price))
        discount = Decimal(str(self.discount_pct)) / Decimal('100')

        self.subtotal = round(qty * price * (1 - discount), 2)

        if include_taxes:
            self.ieps_amount = round(self.subtotal * Decimal(str(ieps_rate)), 2)
            self.iva_amount = round(self.subtotal * Decimal(str(iva_rate)), 2)
        else:
            self.ieps_amount = Decimal('0.00')
            self.iva_amount = Decimal('0.00')

        self.line_total = self.subtotal + self.ieps_amount + self.iva_amount
