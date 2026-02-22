"""
Client Model - B2B/B2C customer management.

Purpose: Track customers with credit control and pricing tier assignment.
Supports the Double-Gate Credit Control business rule.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Index
from database import Base
from datetime import datetime
from decimal import Decimal


class Client(Base):
    """
    Client/Customer model for B2B and B2C sales.

    Business Rules:
    - Each client has a pricing_tier for volume discounts
    - credit_limit enforces financial gate (Double-Gate Credit Control)
    - max_kegs enforces asset gate (keg balance limit)
    - Soft-delete via is_active flag
    """
    __tablename__ = "clients"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identification
    client_code = Column(String(20), unique=True, nullable=False, index=True)
    business_name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(300), nullable=True)
    rfc = Column(String(20), nullable=True, index=True)  # Tax ID (Mexico)

    # Classification
    client_type = Column(String(20), nullable=False, default="B2B")  # B2B, B2C, DISTRIBUTOR
    pricing_tier = Column(String(20), nullable=False, default="RETAIL")  # PLATINUM, GOLD, SILVER, RETAIL

    # Contact
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    contact_person = Column(String(200), nullable=True)

    # Credit control (Double-Gate)
    credit_limit = Column(Numeric(12, 2), nullable=True, default=0)
    current_balance = Column(Numeric(12, 2), nullable=False, default=0)  # Outstanding debt
    max_kegs = Column(Integer, nullable=True)  # Max kegs allowed at client location
    current_kegs = Column(Integer, nullable=False, default=0)  # Kegs currently at client

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    notes = Column(String(1000), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_client_type_tier', 'client_type', 'pricing_tier'),
        Index('idx_client_active_name', 'is_active', 'business_name'),
    )

    def __repr__(self):
        return f"<Client(code='{self.client_code}', name='{self.business_name}', tier='{self.pricing_tier}')>"

    @property
    def available_credit(self) -> Decimal:
        """Remaining credit available."""
        if self.credit_limit is None:
            return Decimal('0.00')
        return Decimal(str(self.credit_limit)) - Decimal(str(self.current_balance))

    @property
    def available_kegs(self) -> int:
        """Remaining keg capacity at client."""
        if self.max_kegs is None:
            return 999  # No limit
        return self.max_kegs - self.current_kegs

    def can_place_order(self, order_amount: Decimal, kegs_requested: int = 0) -> tuple[bool, list[str]]:
        """
        Double-Gate Credit Control check.

        Returns:
            (can_order, list_of_blocking_reasons)
        """
        reasons = []

        # Gate 1: Financial
        if self.credit_limit and (Decimal(str(self.current_balance)) + order_amount) > Decimal(str(self.credit_limit)):
            reasons.append(
                f"Credit limit exceeded: balance ${self.current_balance} + order ${order_amount} > limit ${self.credit_limit}"
            )

        # Gate 2: Assets (kegs)
        if self.max_kegs and (self.current_kegs + kegs_requested) > self.max_kegs:
            reasons.append(
                f"Keg limit exceeded: current {self.current_kegs} + requested {kegs_requested} > max {self.max_kegs}"
            )

        return (len(reasons) == 0, reasons)
