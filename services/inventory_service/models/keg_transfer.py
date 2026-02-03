"""
KegTransfer model - Transfers de contenido entre barriles.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from database import Base


class KegTransfer(Base):
    """
    Transfer de cerveza entre barriles.
    
    Ejemplo: 60L → 2×30L
    """
    __tablename__ = "keg_transfers"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source
    source_keg_id = Column(UUID(as_uuid=True), ForeignKey("keg_assets.id"), nullable=False, index=True)
    source_batch_id = Column(Integer, nullable=True, index=True)
    
    # Targets (JSON array of UUIDs)
    target_keg_ids = Column(JSONB, nullable=False)
    
    # Volumes
    volume_transferred_liters = Column(Numeric(6, 2), nullable=False)
    
    # Tracking
    transferred_by = Column(Integer, nullable=True)
    transferred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(String(500), nullable=True)
    
    def __repr__(self):
        return (
            f"<KegTransfer("
            f"source={self.source_keg_id}, "
            f"volume={self.volume_transferred_liters}L, "
            f"targets={len(self.target_keg_ids) if self.target_keg_ids else 0}"
            f")>"
        )
