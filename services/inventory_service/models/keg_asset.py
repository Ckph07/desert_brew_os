"""
KegAsset model - Barriles como activos fijos individuales.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base


class KegAsset(Base):
    """
    Barril como activo fijo individual con FSM.
    
    Cada barril es único y se trackea durante todo su ciclo de vida.
    """
    __tablename__ = "keg_assets"
    
    # Primary key (UUID)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificación física
    serial_number = Column(String(50), nullable=False, unique=True, index=True)
    rfid_tag = Column(String(100), nullable=True, unique=True, index=True)
    
    # Especificaciones
    size_liters = Column(Integer, nullable=False)  # 20, 30, 50, 60
    material = Column(String(50), nullable=False, default="STAINLESS_STEEL")
    keg_type = Column(String(50), nullable=False, default="SANKE_D")
    
    # Estado actual (FSM)
    current_state = Column(String(20), nullable=False, default="EMPTY", index=True)
    production_batch_id = Column(Integer, nullable=True, index=True)
    
    # Propiedad
    ownership = Column(String(20), nullable=False, default="OWN")
    guest_brewery_id = Column(Integer, nullable=True)
    
    # Ciclo de vida
    cycle_count = Column(Integer, nullable=False, default=0)
    last_cleaned_at = Column(DateTime, nullable=True)
    last_filled_at = Column(DateTime, nullable=True)
    
    # Ubicación y cliente
    current_location = Column(String(100), nullable=True)
    client_id = Column(Integer, nullable=True, index=True)
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True)
    needs_maintenance = Column(Boolean, nullable=False, default=False)
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transitions = relationship("KegTransition", back_populates="keg", order_by="desc(KegTransition.timestamp)")
    
    # Indexes
    __table_args__ = (
        Index('idx_keg_state_location', 'current_state', 'current_location'),
        Index('idx_keg_batch', 'production_batch_id'),
    )
    
    def __repr__(self):
        return (
            f"<KegAsset("
            f"serial='{self.serial_number}', "
            f"state={self.current_state}, "
            f"size={self.size_liters}L"
            f")>"
        )
    
    @property
    def is_available(self) -> bool:
        """Check if keg is available for use."""
        return self.is_active and self.current_state in ["EMPTY", "CLEAN"]
    
    @property
    def is_filled(self) -> bool:
        """Check if keg has beer."""
        return self.current_state in ["FULL", "TAPPED", "IN_CLIENT", "IN_TRANSIT"]
