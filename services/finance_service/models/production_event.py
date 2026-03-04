"""Persisted event inbox for Production events consumed from RabbitMQ."""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

from database import Base


class ProductionEvent(Base):
    """Stores production-domain events consumed asynchronously."""

    __tablename__ = "production_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    routing_key = Column(String(120), nullable=False, index=True)
    event_name = Column(String(120), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    consumed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
