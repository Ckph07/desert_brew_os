"""
KegTransition model - Log inmutable de cambios de estado.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from database import Base


class KegTransition(Base):
    """
    Log inmutable de transiciones de estado de barriles.
    
    Audit trail completo de todos los cambios de estado.
    """
    __tablename__ = "keg_transitions"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Keg reference
    keg_id = Column(UUID(as_uuid=True), ForeignKey("keg_assets.id"), nullable=False, index=True)
    
    # Transition
    from_state = Column(String(20), nullable=False)
    to_state = Column(String(20), nullable=False, index=True)
    
    # Context
    location = Column(String(100), nullable=True)
    user_id = Column(Integer, nullable=True)
    reason = Column(String(200), nullable=True)
    notes = Column(String(500), nullable=True)
    
    # Metadata
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    bulk_operation_id = Column(String(50), nullable=True, index=True)
    
    # Relationships
    keg = relationship("KegAsset", back_populates="transitions")
    
    # Indexes
    __table_args__ = (
        Index('idx_transition_keg_time', 'keg_id', 'timestamp'),
        Index('idx_transition_bulk', 'bulk_operation_id'),
    )
    
    def __repr__(self):
        return (
            f"<KegTransition("
            f"keg_id={self.keg_id}, "
            f"{self.from_state}→{self.to_state}, "
            f"at={self.timestamp}"
            f")>"
        )
