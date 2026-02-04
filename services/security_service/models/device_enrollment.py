"""
Device Enrollment Model - Cryptographic Identity Tracking.

Purpose: Register and manage mobile devices authorized for offline operations.
Each device stores a public Ed25519 key for signature verification.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, text
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
import enum


class DeviceStatus(str, enum.Enum):
    """Device lifecycle states."""
    PENDING = "pending"          # Awaiting admin approval
    ACTIVE = "active"            # Operational
    REVOKED = "revoked"          # Compromised or lost
    SUSPENDED = "suspended"      # Temporarily disabled


class DeviceEnrollment(Base):
    """
    Tracks mobile devices with Ed25519 cryptographic identity.
    
    Security Model:
    - Private key NEVER touches backend (stored in mobile secure enclave)
    - Only public key is registered
    - Signatures verified server-side for non-repudiation
    
    Workflow:
    1. Mobile app generates Ed25519 keypair
    2. Sends public_key + device_id to /enroll
    3. Admin approves via /approve
    4. Device can now sign PoD payloads offline
    """
    __tablename__ = "device_enrollments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    
    # Device Identity
    device_id = Column(String(100), unique=True, nullable=False, index=True)  # IMEI or serial
    device_model = Column(String(100))  # "iPhone 13 Pro", "Samsung Galaxy S21"
    os_version = Column(String(50))     # "iOS 16.2", "Android 13"
    
    # Cryptographic Identity
    public_key_ed25519 = Column(String(128), nullable=False)  # Hex-encoded (64 bytes)
    
    # Ownership
    assigned_user_id = Column(Integer, nullable=False, index=True)
    assigned_user_name = Column(String(200))  # Denormalized for audit
    
    # Status
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.PENDING, nullable=False, index=True)
    
    # Lifecycle Timestamps
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime)
    approved_by_user_id = Column(Integer)
    last_heartbeat = Column(DateTime, index=True)  # Device check-in
    revoked_at = Column(DateTime)
    revoked_reason = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DeviceEnrollment(device_id='{self.device_id}', status='{self.status}', user={self.assigned_user_name})>"
    
    @property
    def is_active(self) -> bool:
        """Check if device can sign payloads."""
        return self.status == DeviceStatus.ACTIVE
    
    @property
    def days_since_heartbeat(self) -> int:
        """Days since last check-in."""
        if not self.last_heartbeat:
            return 999
        return (datetime.utcnow() - self.last_heartbeat).days
