"""
Supplier model for tracking ingredient suppliers.
"""
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Supplier(Base):
    """
    Supplier/Provider model for raw materials and ingredients.
    
    Tracks contact info, payment terms, and quality ratings.
    """
    __tablename__ = "suppliers"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identity
    name = Column(String(200), nullable=False, index=True)
    legal_name = Column(String(300), nullable=True)
    rfc = Column(String(20), nullable=True, index=True)  # Tax ID (Mexico)
    
    # Contact information
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    contact_person = Column(String(200), nullable=True)
    
    # Business terms
    payment_terms = Column(String(100), nullable=True)  # "30 días", "Contado"
    credit_limit = Column(Numeric(12, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    preferred = Column(Boolean, nullable=False, default=False)
    
    # Quality ratings (1-5 scale)
    quality_rating = Column(Numeric(3, 2), nullable=True)  # Product quality
    delivery_rating = Column(Numeric(3, 2), nullable=True)  # On-time delivery
    
    # Notes
    notes = Column(String(1000), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_batches = relationship("StockBatch", back_populates="supplier")
    
    # Indexes
    __table_args__ = (
        Index('idx_active_suppliers', 'is_active', 'name'),
    )
    
    def __repr__(self):
        return f"<Supplier(name='{self.name}', active={self.is_active})>"
