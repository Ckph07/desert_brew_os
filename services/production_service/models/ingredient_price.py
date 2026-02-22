"""
IngredientPrice Model — Reference pricing for production ingredients.

Purpose: CRUD table for ingredient reference prices.
The actual costs used in FIFO come from Inventory Service StockBatch.unit_cost,
but this table allows operators to maintain and view a price list they can
update as suppliers change prices. Also useful for recipe costing simulations.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Index
from database import Base
from datetime import datetime


class IngredientPrice(Base):
    """
    Reference price list for production ingredients.

    Categories: MALT, HOP, YEAST, ADJUNCT, CHEMICAL, PACKAGING, OTHER
    """
    __tablename__ = "ingredient_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identity
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    # MALT, HOP, YEAST, ADJUNCT, CHEMICAL, PACKAGING, OTHER

    # Pricing
    unit_measure = Column(String(20), nullable=False)
    # KG, G, L, ML, PACKET, UNIT
    current_price = Column(Numeric(10, 2), nullable=False)
    # Price per unit_measure in MXN
    currency = Column(String(3), nullable=False, default="MXN")

    # Supplier reference
    supplier_name = Column(String(200), nullable=True)
    supplier_sku = Column(String(100), nullable=True)

    # Metadata
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(String(500), nullable=True)
    last_price_update = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_ingredient_category_name', 'category', 'name'),
    )

    def __repr__(self):
        return f"<IngredientPrice(name='{self.name}', category='{self.category}', price=${self.current_price}/{self.unit_measure})>"
