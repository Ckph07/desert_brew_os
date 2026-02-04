"""
Unit tests for SignatureVerifier logic.
"""
import pytest
import json
from datetime import datetime, timedelta
from logic.signature_verifier import SignatureVerifier
from models.device_enrollment import DeviceEnrollment, DeviceStatus


class TestSignatureVerifier:
    """Test Ed25519 signature verification."""
    
    def test_verify_valid_signature(self, db_session, ed25519_keypair):
        """Test verification of valid signature."""
        # Create enrolled device
        device = DeviceEnrollment(
            device_id="SIG-TEST-001",
            device_model="iPhone",
            os_version="iOS 17",
            public_key_ed25519=ed25519_keypair["public_key_hex"],
            assigned_user_id=1,
            assigned_user_name="Test User",
            status=DeviceStatus.ACTIVE
        )
        db_session.add(device)
        db_session.commit()
        
        # Create payload
        payload = {
            "order_id": 123,
            "items": [{"sku": "BEER-IPA-KEG", "qty": 10}],
            "timestamp": datetime.utcnow().isoformat(),
            "gps": {"lat": 25.4232, "lon": -101.0053}
        }
        
        # Sign payload
        message = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = ed25519_keypair["signing_key"].sign(message).signature.hex()
        
        # Verify
        is_valid, error = SignatureVerifier.verify_pod_signature(
            payload=payload,
            signature_hex=signature,
            device_id="SIG-TEST-001",
            db=db_session
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_verify_invalid_signature(self, db_session, ed25519_keypair):
        """Test verification fails for invalid signature."""
        # Create device
        device = DeviceEnrollment(
            device_id="SIG-TEST-002",
            device_model="Android",
            os_version="Android 13",
            public_key_ed25519=ed25519_keypair["public_key_hex"],
            assigned_user_id=2,
            assigned_user_name="Test User 2",
            status=DeviceStatus.ACTIVE
        )
        db_session.add(device)
        db_session.commit()
        
        # Create payload
        payload = {
            "order_id": 456,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Use WRONG signature (just random hex)
        fake_signature = "a" * 128
        
        # Verify
        is_valid, error = SignatureVerifier.verify_pod_signature(
            payload=payload,
            signature_hex=fake_signature,
            device_id="SIG-TEST-002",
            db=db_session
        )
        
        assert is_valid is False
        assert "cryptographic verification failed" in error
    
    def test_verify_device_not_enrolled(self, db_session):
        """Test verification fails for non-enrolled device."""
        payload = {"timestamp": datetime.utcnow().isoformat()}
        signature = "b" * 128
        
        is_valid, error = SignatureVerifier.verify_pod_signature(
            payload=payload,
            signature_hex=signature,
            device_id="NON-EXISTENT",
            db=db_session
        )
        
        assert is_valid is False
        assert "not enrolled" in error
    
    def test_verify_device_not_active(self, db_session, ed25519_keypair):
        """Test verification fails for non-active device."""
        # Create PENDING device
        device = DeviceEnrollment(
            device_id="SIG-TEST-003",
            device_model="iPhone",
            os_version="iOS 16",
            public_key_ed25519=ed25519_keypair["public_key_hex"],
            assigned_user_id=3,
            assigned_user_name="Pending User",
            status=DeviceStatus.PENDING  # Not ACTIVE
        )
        db_session.add(device)
        db_session.commit()
        
        payload = {"timestamp": datetime.utcnow().isoformat()}
        signature = "c" * 128
        
        is_valid, error = SignatureVerifier.verify_pod_signature(
            payload=payload,
            signature_hex=signature,
            device_id="SIG-TEST-003",
            db=db_session
        )
        
        assert is_valid is False
        assert "pending" in error.lower()
    
    def test_verify_expired_timestamp(self, db_session, ed25519_keypair):
        """Test verification fails for old timestamp (replay attack)."""
        device = DeviceEnrollment(
            device_id="SIG-TEST-004",
            device_model="iPhone",
            os_version="iOS 17",
            public_key_ed25519=ed25519_keypair["public_key_hex"],
            assigned_user_id=4,
            assigned_user_name="Test User 4",
            status=DeviceStatus.ACTIVE
        )
        db_session.add(device)
        db_session.commit()
        
        # Create payload with OLD timestamp (10 minutes ago)
        old_timestamp = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        payload = {
            "order_id": 789,
            "timestamp": old_timestamp  # Too old
        }
        
        # Sign with correct key
        message = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = ed25519_keypair["signing_key"].sign(message).signature.hex()
        
        # Verify
        is_valid, error = SignatureVerifier.verify_pod_signature(
            payload=payload,
            signature_hex=signature,
            device_id="SIG-TEST-004",
            db=db_session
        )
        
        assert is_valid is False
        assert "too old" in error.lower()
    
    def test_verify_missing_timestamp(self, db_session, ed25519_keypair):
        """Test verification fails if payload missing timestamp."""
        device = DeviceEnrollment(
            device_id="SIG-TEST-005",
            device_model="iPhone",
            os_version="iOS 17",
            public_key_ed25519=ed25519_keypair["public_key_hex"],
            assigned_user_id=5,
            assigned_user_name="Test User 5",
            status=DeviceStatus.ACTIVE
        )
        db_session.add(device)
        db_session.commit()
        
        # Payload without timestamp
        payload = {"order_id": 999}  # Missing 'timestamp'
        
        message = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = ed25519_keypair["signing_key"].sign(message).signature.hex()
        
        is_valid, error = SignatureVerifier.verify_pod_signature(
            payload=payload,
            signature_hex=signature,
            device_id="SIG-TEST-005",
            db=db_session
        )
        
        assert is_valid is False
        assert "missing" in error.lower() and "timestamp" in error.lower()
    
    def test_verify_signature_only(self, ed25519_keypair):
        """Test static signature verification without database."""
        message = b"Test message"
        signature = ed25519_keypair["signing_key"].sign(message).signature.hex()
        
        # Valid signature
        result = SignatureVerifier.verify_signature_only(
            message=message,
            signature_hex=signature,
            public_key_hex=ed25519_keypair["public_key_hex"]
        )
        assert result is True
        
        # Invalid signature
        result = SignatureVerifier.verify_signature_only(
            message=message,
            signature_hex="z" * 128,  # Wrong signature
            public_key_hex=ed25519_keypair["public_key_hex"]
        )
        assert result is False
