"""
Cold Room Temperature Monitoring.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Index
from database import Base
from datetime import datetime
from decimal import Decimal


class ColdRoomReading(Base):
    """
    Temperature and humidity readings from cold rooms.
    
    Tracks environmental conditions to ensure product quality.
    Readings should be taken every 15 minutes (automated sensors).
    
    Alerts trigger when:
    - Temperature > 7°C
    - Temperature < 0°C
    - Humidity > 80%
    """
    __tablename__ = "cold_room_readings"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Location
    cold_room_id = Column(String(50), nullable=False, index=True)  # ColdRoomLocation enum
    
    # Readings
    temperature_celsius = Column(Numeric(5, 2), nullable=False)
    humidity_percent = Column(Numeric(5, 2), nullable=True)
    
    # Alert status
    alert_triggered = Column(Boolean, nullable=False, default=False)
    alert_reason = Column(String(200), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Indexes for fast querying
    __table_args__ = (
        Index('idx_cr_room_time', 'cold_room_id', 'timestamp'),
        Index('idx_cr_alerts', 'alert_triggered', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ColdRoomReading(room='{self.cold_room_id}', temp={self.temperature_celsius}°C, time={self.timestamp})>"
    
    @staticmethod
    def check_alert_conditions(
        temperature: Decimal,
        humidity: Decimal = None
    ) -> tuple[bool, str]:
        """
        Check if reading should trigger an alert.
        
        Returns:
            (alert_triggered, alert_reason)
        """
        # Temperature alerts
        if temperature > Decimal('7.0'):
            return (True, f"Temperature too high: {temperature}°C (max: 7°C)")
        
        if temperature < Decimal('0.0'):
            return (True, f"Temperature too low: {temperature}°C (min: 0°C)")
        
        # Humidity alerts
        if humidity and humidity > Decimal('80.0'):
            return (True, f"Humidity too high: {humidity}% (max: 80%)")
        
        return (False, None)
    
    @classmethod
    def create_reading(
        cls,
        cold_room_id: str,
        temperature: Decimal,
        humidity: Decimal = None
    ) -> 'ColdRoomReading':
        """
        Create a new reading with automatic alert checking.
        
        Args:
            cold_room_id: Room identifier
            temperature: Temperature in Celsius
            humidity: Optional humidity percentage
            
        Returns:
            ColdRoomReading instance
        """
        alert_triggered, alert_reason = cls.check_alert_conditions(temperature, humidity)
        
        return cls(
            cold_room_id=cold_room_id,
            temperature_celsius=temperature,
            humidity_percent=humidity,
            alert_triggered=alert_triggered,
            alert_reason=alert_reason
        )
