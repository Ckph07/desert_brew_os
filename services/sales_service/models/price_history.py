"""
Price History Model - Track price changes over time.

Purpose: Maintain audit trail of all price changes per product and channel.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index
from database import Base
from datetime import datetime


class PriceHistory(Base):
    """
    Price change audit trail.

    Records every price change for compliance and analysis.
    """
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("product_catalog.id"), nullable=False, index=True)
    channel = Column(String(20), nullable=False)  # "FIXED", "TAPROOM", "DISTRIBUTOR", etc.
    old_price = Column(Numeric(10, 2), nullable=True)
    new_price = Column(Numeric(10, 2), nullable=False)
    change_reason = Column(String(200), nullable=True)
    changed_by = Column(String(100), nullable=True)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_price_history_product_channel', 'product_id', 'channel'),
        Index('idx_price_history_date', 'changed_at'),
    )

    def __repr__(self):
        return f"<PriceHistory(product={self.product_id}, channel='{self.channel}', ${self.old_price}→${self.new_price})>"
