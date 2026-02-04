"""
Integration tests for signature verification API.
"""
import pytest
import json
from datetime import datetime
from nacl.signing import SigningKey


class TestSignatureVerificationAPI:
    """Test signature verification endpoint."""
    
    def test_verify_signature_success(self, client, ed25519_keypair):
        """Test successful signature verification via API."""
        # Enroll and approve device
        enroll_data = {
            "device_id": "API-SIG-001",
            "device_model": "iPhone 14",
            "os_version": "iOS 17",
            "public_key_hex": ed25519_keypair["public_key_hex"],
            "user_id": 10,
            "user_name": "API Test User"
        }
        client.post("/api/v1/security/enroll", json=enroll_data)
        client.patch(
            "/api/v1/security/enrollments/API-SIG-001/approve",
            json={"admin_user_id": 1}
        )
        
        # Create and sign payload
        payload = {
            "order_id": 123,
            "items": [{"sku": "BEER-IPA", "qty": 10}],
            "timestamp": datetime.utcnow().isoformat(),
            "gps": {"lat": 25.4, "lon": -101.0}
        }
        
        message = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = ed25519_keypair["signing_key"].sign(message).signature.hex()
        
        # Verify via API
        verify_request = {
            "device_id": "API-SIG-001",
            "payload": payload,
            "signature_hex": signature
        }
        
        response = client.post(
            "/api/v1/security/verify-signature",
            json=verify_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["error_message"] is None
        assert data["device_id"] == "API-SIG-001"
    
    def test_verify_signature_invalid(self, client, ed25519_keypair):
        """Test verification fails for invalid signature."""
        # Enroll and approve
        enroll_data = {
            "device_id": "API-SIG-002",
            "device_model": "Android",
            "os_version": "Android 13",
            "public_key_hex": ed25519_keypair["public_key_hex"],
            "user_id": 11,
            "user_name": "Test User 2"
        }
        client.post("/api/v1/security/enroll", json=enroll_data)
        client.patch(
            "/api/v1/security/enrollments/API-SIG-002/approve",
            json={"admin_user_id": 1}
        )
        
        # Create payload with WRONG signature
        payload = {
            "order_id": 456,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        verify_request = {
            "device_id": "API-SIG-002",
            "payload": payload,
            "signature_hex": "a" * 128  # Invalid signature
        }
        
        response = client.post(
            "/api/v1/security/verify-signature",
            json=verify_request
        )
        
        assert response.status_code == 200  # API returns 200 but is_valid=False
        data = response.json()
        assert data["is_valid"] is False
        assert data["error_message"] is not None
        assert "failed" in data["error_message"].lower()
