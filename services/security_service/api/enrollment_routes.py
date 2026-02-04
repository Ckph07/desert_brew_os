"""
FastAPI routes for Device Enrollment and Signature Verification.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from database import get_db
from models.device_enrollment import DeviceEnrollment, DeviceStatus
from schemas.device import (
    DeviceEnrollRequest,
    DeviceEnrollResponse,
    DeviceApprovalRequest,
    DeviceHeartbeatResponse,
    DeviceListResponse,
    SignatureVerificationRequest,
    SignatureVerificationResponse
)
from logic.signature_verifier import SignatureVerifier

router = APIRouter(prefix="/api/v1/security", tags=["Security"])


@router.post("/enroll", response_model=DeviceEnrollResponse, status_code=201)
def enroll_device(
    enrollment: DeviceEnrollRequest,
    db: Session = Depends(get_db)
):
    """
    Request device enrollment.
    
    Flow:
    1. Mobile app generates Ed25519 keypair
    2. Sends public_key + device_id to this endpoint
    3. Admin reviews and approves via PATCH /enrollments/{id}/approve
    4. Device transitions to ACTIVE status
    """
    # Check if device already enrolled
    existing = db.query(DeviceEnrollment).filter_by(
        device_id=enrollment.device_id
    ).first()
    
    if existing:
        if existing.status == DeviceStatus.ACTIVE:
            raise HTTPException(
                status_code=409,
                detail=f"Device '{enrollment.device_id}' already enrolled and active"
            )
        elif existing.status == DeviceStatus.REVOKED:
            raise HTTPException(
                status_code=403,
                detail=f"Device '{enrollment.device_id}' was revoked. Contact administrator."
            )
        elif existing.status == DeviceStatus.PENDING:
            raise HTTPException(
                status_code=409,
                detail=f"Device '{enrollment.device_id}' already has pending enrollment request"
            )
    
    # Create enrollment request
    device = DeviceEnrollment(
        device_id=enrollment.device_id,
        device_model=enrollment.device_model,
        os_version=enrollment.os_version,
        public_key_ed25519=enrollment.public_key_hex,
        assigned_user_id=enrollment.user_id,
        assigned_user_name=enrollment.user_name,
        status=DeviceStatus.PENDING
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return DeviceEnrollResponse(
        id=str(device.id),
        device_id=device.device_id,
        device_model=device.device_model,
        status=device.status.value,
        assigned_user_name=device.assigned_user_name,
        enrolled_at=device.enrolled_at
    )


@router.patch("/enrollments/{device_id}/approve")
def approve_enrollment(
    device_id: str,
    approval: DeviceApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Admin-only: Approve pending enrollment.
    
    TODO: Add RBAC check for admin role.
    """
    device = db.query(DeviceEnrollment).filter_by(device_id=device_id).first()
    
    if not device:
        raise HTTPException(404, f"Device '{device_id}' not found")
    
    if device.status != DeviceStatus.PENDING:
        raise HTTPException(
            400,
            f"Cannot approve device with status: {device.status.value}"
        )
    
    device.status = DeviceStatus.ACTIVE
    device.approved_at = datetime.utcnow()
    device.approved_by_user_id = approval.admin_user_id
    
    db.commit()
    
    return {
        "message": f"Device '{device_id}' approved",
        "public_key": device.public_key_ed25519,
        "assigned_user": device.assigned_user_name,
        "status": device.status.value
    }


@router.patch("/enrollments/{device_id}/revoke")
def revoke_device(
    device_id: str,
    reason: str,
    admin_user_id: int,
    db: Session = Depends(get_db)
):
    """
    Admin-only: Revoke a device (compromised or lost).
    """
    device = db.query(DeviceEnrollment).filter_by(device_id=device_id).first()
    
    if not device:
        raise HTTPException(404, f"Device '{device_id}' not found")
    
    if device.status == DeviceStatus.REVOKED:
        raise HTTPException(400, f"Device already revoked")
    
    device.status = DeviceStatus.REVOKED
    device.revoked_at = datetime.utcnow()
    device.revoked_reason = reason
    
    db.commit()
    
    return {
        "message": f"Device '{device_id}' revoked",
        "reason": reason
    }


@router.post("/enrollments/{device_id}/heartbeat", response_model=DeviceHeartbeatResponse)
def device_heartbeat(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Device check-in to maintain active status.
    
    Mobile apps should call this every 24h.
    """
    device = db.query(DeviceEnrollment).filter_by(device_id=device_id).first()
    
    if not device:
        raise HTTPException(404, f"Device '{device_id}' not enrolled")
    
    device.last_heartbeat = datetime.utcnow()
    db.commit()
    
    return DeviceHeartbeatResponse(
        device_id=device.device_id,
        device_status=device.status.value,
        last_heartbeat=device.last_heartbeat
    )


@router.get("/enrollments", response_model=List[DeviceListResponse])
def list_devices(
    status: DeviceStatus = Query(None, description="Filter by status"),
    user_id: int = Query(None, description="Filter by user"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List all enrolled devices (admin view)."""
    query = db.query(DeviceEnrollment)
    
    if status:
        query = query.filter(DeviceEnrollment.status == status)
    
    if user_id:
        query = query.filter(DeviceEnrollment.assigned_user_id == user_id)
    
    devices = query.order_by(DeviceEnrollment.enrolled_at.desc()).offset(skip).limit(limit).all()
    
    return [
        DeviceListResponse(
            id=str(d.id),
            device_id=d.device_id,
            device_model=d.device_model,
            assigned_user_name=d.assigned_user_name,
            status=d.status.value,
            enrolled_at=d.enrolled_at,
            last_heartbeat=d.last_heartbeat,
            days_since_heartbeat=d.days_since_heartbeat
        )
        for d in devices
    ]


@router.post("/verify-signature", response_model=SignatureVerificationResponse)
def verify_signature(
    request: SignatureVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a signed payload (typically for Proof of Delivery).
    
    Returns 200 OK even if signature invalid (check is_valid field).
    """
    is_valid, error_msg = SignatureVerifier.verify_pod_signature(
        payload=request.payload,
        signature_hex=request.signature_hex,
        device_id=request.device_id,
        db=db
    )
    
    return SignatureVerificationResponse(
        is_valid=is_valid,
        error_message=error_msg if not is_valid else None,
        device_id=request.device_id,
        verified_at=datetime.utcnow()
    )


@router.get("/enrollments/stats")
def get_enrollment_stats(db: Session = Depends(get_db)):
    """Get enrollment statistics (admin dashboard)."""
    stats = db.query(
        DeviceEnrollment.status,
        func.count(DeviceEnrollment.id).label('count')
    ).group_by(DeviceEnrollment.status).all()
    
    stats_dict = {status.value: count for status, count in stats}
    
    # Devices without heartbeat in >7 days
    stale_count = db.query(DeviceEnrollment).filter(
        DeviceEnrollment.status == DeviceStatus.ACTIVE,
        DeviceEnrollment.last_heartbeat < datetime.utcnow() - timedelta(days=7)
    ).count()
    
    return {
        "by_status": stats_dict,
        "total": sum(stats_dict.values()),
        "stale_devices_7d": stale_count
    }
