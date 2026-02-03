"""
StockBatch model - Materia Prima con FIFO tracking.
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from database import Base


class StockBatch(Base):
    """
    Representa un lote de materia prima recibido de un proveedor.
    
    La rotación FIFO se implementa ordenando por arrival_date ASC.
    """
    __tablename__ = "stock_batches"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificación del producto
    sku = Column(String(50), nullable=False, index=True)
    batch_number = Column(String(100), nullable=True)
    category = Column(String(20), nullable=False)  # MALT, HOPS, YEAST, etc.
    
    # Fechas críticas para FIFO y caducidad
    arrival_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expiration_date = Column(DateTime, nullable=True)
    
    # Cantidades (usando Numeric para precision con decimales)
    initial_quantity = Column(Numeric(10, 3), nullable=False)
    remaining_quantity = Column(Numeric(10, 3), nullable=False)
    unit_measure = Column(String(10), nullable=False)  # KG, G, L, ML, UNIT
    
    # Costos en MXN
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    
    # Información del proveedor (legacy)
    provider_id = Column(String(50), nullable=True)
    provider_name = Column(String(200), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    
    # Ubicación física en almacén
    location = Column(String(100), nullable=True)
    
    # Supplier tracking (nuevo)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    purchase_order = Column(String(100), nullable=True)
    
    # Estado del lote
    is_allocated = Column(Boolean, default=False)  # True cuando remaining = 0
    lock_version = Column(Integer, default=1)  # Para optimistic locking
    
    # Metadata timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="stock_batches")
    
    # Índices compuestos para optimizar queries FIFO
    __table_args__ = (
        # CRITICAL: Este índice es esencial para performance de FIFO
        Index(
            'idx_fifo_query',
            'sku',
            'arrival_date',
            postgresql_where=(Column('remaining_quantity') > 0)
        ),
        Index('idx_category_sku', 'category', 'sku'),
        Index('idx_supplier_date', 'supplier_id', 'arrival_date'),
    )
    
    def __repr__(self):
        return (
            f"<StockBatch("
            f"id={self.id}, "
            f"sku='{self.sku}', "
            f"batch='{self.batch_number}', "
            f"remaining={self.remaining_quantity} {self.unit_measure}"
            f")>"
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if batch has expired."""
        if self.expiration_date is None:
            return False
        return datetime.utcnow() > self.expiration_date
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate how much of the batch has been used."""
        if self.initial_quantity == 0:
            return 0.0
        used = self.initial_quantity - self.remaining_quantity
        return float((used / self.initial_quantity) * 100)
