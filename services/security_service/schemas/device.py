"""
Pydantic schemas for Device Enrollment requests/responses.
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import re


class DeviceEnrollRequest(BaseModel):
    """Request to enroll a new device."""
    device_id: str = Field(..., min_length=5, max_length=100, description="Unique device identifier (IMEI/serial)")
    device_model: str = Field(..., max_length=100, description="Device model (e.g., 'iPhone 14 Pro')")
    os_version: str = Field(..., max_length=50, description="OS version (e.g., 'iOS 17.2')")
    public_key_hex: str = Field(..., min_length=64, max_length=128, description="Ed25519 public key (hex-encoded)")
    user_id: int = Field(..., gt=0, description="User ID to assign device to")
    user_name: str = Field(..., min_length=1, max_length=200, description="User full name")
    
    @validator('public_key_hex')
    def validate_hex(cls, v):
        """Ensure public key is valid hex."""
        if not re.match(r'^[0-9a-fA-F]+$', v):
            raise ValueError('public_key_hex must be hexadecimal')
        if len(v) != 64:  # 32 bytes * 2 hex chars
            raise ValueError('Ed25519 public key must be 64 hex characters (32 bytes)')
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "IMEI:123456789012345",
                "device_model": "iPhone 14 Pro",
                "os_version": "iOS 17.2",
                "public_key_hex": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
                "user_id": 5,
                "user_name": "Juan Vendedor"
            }
        }


class DeviceEnrollResponse(BaseModel):
    """Response after enrollment request."""
    id: str
    device_id: str
    device_model: str
    status: str
    assigned_user_name: str
    enrolled_at: datetime
    message: str = "Enrollment request submitted. Awaiting approval."
    
    class Config:
        orm_mode = True


class DeviceApprovalRequest(BaseModel):
    """Request to approve a pending device."""
    admin_user_id: int = Field(..., gt=0, description="Admin approving the device")


class DeviceHeartbeatResponse(BaseModel):
    """Response from heartbeat check-in."""
    device_id: str
    device_status: str
    last_heartbeat: datetime
    message: str = "Heartbeat recorded"


class DeviceListResponse(BaseModel):
    """Device summary in list view."""
    id: str
    device_id: str
    device_model: str
    assigned_user_name: str
    status: str
    enrolled_at: datetime
    last_heartbeat: Optional[datetime]
    days_since_heartbeat: int
    
    class Config:
        orm_mode = True


class SignatureVerificationRequest(BaseModel):
    """Request to verify a signed payload."""
    device_id: str
    payload: dict = Field(..., description="The data that was signed")
    signature_hex: str = Field(..., min_length=128, max_length=128, description="Ed25519 signature (hex)")
    
    @validator('signature_hex')
    def validate_signature_hex(cls, v):
        if not re.match(r'^[0-9a-fA-F]+$', v):
            raise ValueError('signature_hex must be hexadecimal')
        if len(v) != 128:  # 64 bytes * 2
            raise ValueError('Ed25519 signature must be 128 hex characters')
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "IMEI:123456789012345",
                "payload": {
                    "order_id": 123,
                    "items": [{"sku": "BEER-IPA-KEG", "qty": 10}],
                    "timestamp": "2026-02-03T17:45:00",
                    "gps": {"lat": 25.4232, "lon": -101.0053}
                },
                "signature_hex": "a" * 128  # Placeholder
            }
        }


class SignatureVerificationResponse(BaseModel):
    """Response from signature verification."""
    is_valid: bool
    error_message: Optional[str] = None
    device_id: str
    verified_at: datetime
