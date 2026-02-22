"""
Product Catalog Model - SKU management with dual pricing.

Purpose: Track products with both fixed prices (manual) and theoretical prices
(calculated by OS via FIFO + Transfer Pricing) for margin comparison.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Index
from database import Base
from datetime import datetime
from decimal import Decimal


class ProductCatalog(Base):
    """
    Product catalog with dual pricing for margin comparison.

    Business Rules:
    - fixed_price: Set manually by the business (real market price)
    - theoretical_price: Calculated by OS (cost + transfer pricing + markup)
    - Both visible side-by-side for margin analysis
    - Price per channel (taproom, distributor, on/off premise, ecommerce)
    """
    __tablename__ = "product_catalog"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Product identification
    sku = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(200), nullable=False, index=True)
    description = Column(String(500), nullable=True)

    # Classification
    style = Column(String(100), nullable=True)       # "IPA", "Lager", "Amber", "Stout"
    category = Column(String(30), nullable=False)     # "BEER_BOTTLE", "BEER_KEG", "BEER_LITER", "BARREL", "SHIPPING", "MERCH"
    origin_type = Column(String(20), nullable=False, default="HOUSE")  # "HOUSE", "GUEST", "COMMERCIAL"

    # Volume/Format
    volume_ml = Column(Integer, nullable=True)        # 355, 473, 940, 20000 (kegs)
    unit_measure = Column(String(20), nullable=False, default="LITROS")  # "LITROS", "BOTTLES", "KEGS", "UNITS"
    abv = Column(Numeric(4, 2), nullable=True)
    ibu = Column(Integer, nullable=True)

    # === DUAL PRICING (Core Feature) ===
    fixed_price = Column(Numeric(10, 2), nullable=True)        # Precio establecido manualmente
    theoretical_price = Column(Numeric(10, 2), nullable=True)  # Calculado por OS (cost + markup)
    cost_per_unit = Column(Numeric(10, 2), nullable=True)      # Costo unitario (FIFO)

    # Per-channel pricing
    price_taproom = Column(Numeric(10, 2), nullable=True)
    price_distributor = Column(Numeric(10, 2), nullable=True)
    price_on_premise = Column(Numeric(10, 2), nullable=True)
    price_off_premise = Column(Numeric(10, 2), nullable=True)
    price_ecommerce = Column(Numeric(10, 2), nullable=True)

    # Tax rates
    ieps_rate = Column(Numeric(5, 4), nullable=True)   # e.g. 0.5340 MXN/L for >14° GL
    iva_rate = Column(Numeric(5, 4), nullable=True, default=0.16)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    notes = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_product_category_origin', 'category', 'origin_type'),
        Index('idx_product_active_name', 'is_active', 'product_name'),
    )

    def __repr__(self):
        return f"<ProductCatalog(sku='{self.sku}', name='{self.product_name}', fixed=${self.fixed_price})>"

    @property
    def fixed_margin_pct(self) -> float | None:
        """Margin percentage using fixed price."""
        if not self.fixed_price or not self.cost_per_unit or self.cost_per_unit == 0:
            return None
        return float(
            (Decimal(str(self.fixed_price)) - Decimal(str(self.cost_per_unit)))
            / Decimal(str(self.fixed_price)) * 100
        )

    @property
    def theoretical_margin_pct(self) -> float | None:
        """Margin percentage using theoretical (OS-calculated) price."""
        if not self.theoretical_price or not self.cost_per_unit or self.cost_per_unit == 0:
            return None
        return float(
            (Decimal(str(self.theoretical_price)) - Decimal(str(self.cost_per_unit)))
            / Decimal(str(self.theoretical_price)) * 100
        )

    @property
    def margin_delta_pct(self) -> float | None:
        """Difference between fixed and theoretical margins."""
        fm = self.fixed_margin_pct
        tm = self.theoretical_margin_pct
        if fm is None or tm is None:
            return None
        return round(fm - tm, 2)
