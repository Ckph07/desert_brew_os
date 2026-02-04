"""
Unit tests for DeviceEnrollment model and lifecycle.
"""
import pytest
from datetime import datetime, timedelta
from models.device_enrollment import DeviceEnrollment, DeviceStatus


class TestDeviceEnrollmentModel:
    """Test DeviceEnrollment model."""
    
    def test_create_device_enrollment(self, db_session, sample_device_enrollment_data):
        """Test creating a device enrollment."""
        device = DeviceEnrollment(
            device_id=sample_device_enrollment_data["device_id"],
            device_model=sample_device_enrollment_data["device_model"],
            os_version=sample_device_enrollment_data["os_version"],
            public_key_ed25519=sample_device_enrollment_data["public_key_hex"],
            assigned_user_id=sample_device_enrollment_data["user_id"],
            assigned_user_name=sample_device_enrollment_data["user_name"],
            status=DeviceStatus.PENDING
        )
        
        db_session.add(device)
        db_session.commit()
        db_session.refresh(device)
        
        assert device.id is not None
        assert device.device_id == "TEST-DEVICE-001"
        assert device.status == DeviceStatus.PENDING
        assert device.is_active is False
        assert device.enrolled_at is not None
    
    def test_device_status_transitions(self, db_session, sample_device_enrollment_data):
        """Test device status lifecycle."""
        device = DeviceEnrollment(
            device_id="TEST-002",
            device_model="Samsung S21",
            os_version="Android 13",
            public_key_ed25519="b" * 64,
            assigned_user_id=10,
            assigned_user_name="Maria Seller",
            status=DeviceStatus.PENDING
        )
        
        db_session.add(device)
        db_session.commit()
        
        # PENDING → ACTIVE
        device.status = DeviceStatus.ACTIVE
        device.approved_at = datetime.utcnow()
        device.approved_by_user_id = 1
        db_session.commit()
        
        assert device.is_active is True
        assert device.approved_at is not None
        
        # ACTIVE → REVOKED
        device.status = DeviceStatus.REVOKED
        device.revoked_at = datetime.utcnow()
        device.revoked_reason = "Device lost"
        db_session.commit()
        
        assert device.is_active is False
        assert device.revoked_reason == "Device lost"
    
    def test_days_since_heartbeat(self, db_session):
        """Test heartbeat calculation."""
        device = DeviceEnrollment(
            device_id="TEST-003",
            device_model="iPhone 13",
            os_version="iOS 16",
            public_key_ed25519="c" * 64,
            assigned_user_id=15,
            assigned_user_name="Pedro Sales",
            status=DeviceStatus.ACTIVE
        )
        
        # No heartbeat yet
        assert device.days_since_heartbeat == 999
        
        # Recent heartbeat
        device.last_heartbeat = datetime.utcnow()
        db_session.add(device)
        db_session.commit()
        
        assert device.days_since_heartbeat == 0
        
        # Old heartbeat
        device.last_heartbeat = datetime.utcnow() - timedelta(days=10)
        db_session.commit()
        
        assert device.days_since_heartbeat == 10
    
    def test_unique_device_id_constraint(self, db_session):
        """Test that device_id must be unique."""
        device1 = DeviceEnrollment(
            device_id="DUPLICATE-001",
            device_model="iPhone",
            os_version="iOS 17",
            public_key_ed25519="d" * 64,
            assigned_user_id=20,
            assigned_user_name="Test User",
            status=DeviceStatus.PENDING
        )
        
        device2 = DeviceEnrollment(
            device_id="DUPLICATE-001",  # Same ID
            device_model="Android",
            os_version="Android 12",
            public_key_ed25519="e" * 64,
            assigned_user_id=21,
            assigned_user_name="Another User",
            status=DeviceStatus.PENDING
        )
        
        db_session.add(device1)
        db_session.commit()
        
        db_session.add(device2)
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()
