"""
Integration tests for device enrollment API endpoints.
"""
import pytest
import json
from datetime import datetime


class TestEnrollmentAPI:
    """Test device enrollment endpoints."""
    
    def test_enroll_device_success(self, client, sample_device_enrollment_data):
        """Test successful device enrollment."""
        response = client.post(
            "/api/v1/security/enroll",
            json=sample_device_enrollment_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == "TEST-DEVICE-001"
        assert data["status"] == "pending"
        assert data["assigned_user_name"] == "Juan Vendedor"
        assert "id" in data
    
    def test_enroll_duplicate_device(self, client, sample_device_enrollment_data):
        """Test enrolling same device twice fails."""
        # First enrollment
        client.post("/api/v1/security/enroll", json=sample_device_enrollment_data)
        
        # Second enrollment (duplicate)
        response = client.post(
            "/api/v1/security/enroll",
            json=sample_device_enrollment_data
        )
        
        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()
    
    def test_enroll_invalid_public_key(self, client, sample_device_enrollment_data):
        """Test enrollment fails with invalid public key."""
        invalid_data = sample_device_enrollment_data.copy()
        invalid_data["public_key_hex"] = "invalid_hex"  # Not 64 chars
        
        response = client.post(
            "/api/v1/security/enroll",
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_approve_enrollment(self, client, sample_device_enrollment_data):
        """Test approving pending enrollment."""
        # Enroll device
        enroll_response = client.post(
            "/api/v1/security/enroll",
            json=sample_device_enrollment_data
        )
        assert enroll_response.status_code == 201
        
        # Approve
        approve_response = client.patch(
            f"/api/v1/security/enrollments/TEST-DEVICE-001/approve",
            json={"admin_user_id": 1}
        )
        
        assert approve_response.status_code == 200
        data = approve_response.json()
        assert data["status"] == "active"
        assert "public_key" in data
    
    def test_approve_nonexistent_device(self, client):
        """Test approving non-existent device fails."""
        response = client.patch(
            "/api/v1/security/enrollments/NONEXISTENT/approve",
            json={"admin_user_id": 1}
        )
        
        assert response.status_code == 404
    
    def test_revoke_device(self, client, sample_device_enrollment_data):
        """Test revoking a device."""
        # Enroll and approve
        client.post("/api/v1/security/enroll", json=sample_device_enrollment_data)
        client.patch(
            "/api/v1/security/enrollments/TEST-DEVICE-001/approve",
            json={"admin_user_id": 1}
        )
        
        # Revoke
        revoke_response = client.patch(
            "/api/v1/security/enrollments/TEST-DEVICE-001/revoke",
            params={"reason": "Device lost", "admin_user_id": 1}
        )
        
        assert revoke_response.status_code == 200
        assert "revoked" in revoke_response.json()["message"].lower()
    
    def test_device_heartbeat(self, client, sample_device_enrollment_data):
        """Test device heartbeat check-in."""
        # Enroll device
        client.post("/api/v1/security/enroll", json=sample_device_enrollment_data)
        
        # Heartbeat
        heartbeat_response = client.post(
            "/api/v1/security/enrollments/TEST-DEVICE-001/heartbeat"
        )
        
        assert heartbeat_response.status_code == 200
        data = heartbeat_response.json()
        assert data["device_id"] == "TEST-DEVICE-001"
        assert "last_heartbeat" in data
    
    def test_list_devices(self, client, sample_device_enrollment_data):
        """Test listing enrolled devices."""
        # Enroll 2 devices
        client.post("/api/v1/security/enroll", json=sample_device_enrollment_data)
        
        second_device = sample_device_enrollment_data.copy()
        second_device["device_id"] = "TEST-DEVICE-002"
        second_device["public_key_hex"] = "b" * 64
        client.post("/api/v1/security/enroll", json=second_device)
        
        # List all
        list_response = client.get("/api/v1/security/enrollments")
        
        assert list_response.status_code == 200
        devices = list_response.json()
        assert len(devices) == 2
    
    def test_list_devices_filtered_by_status(self, client, sample_device_enrollment_data):
        """Test filtering devices by status."""
        # Enroll and approve one
        client.post("/api/v1/security/enroll", json=sample_device_enrollment_data)
        client.patch(
            "/api/v1/security/enrollments/TEST-DEVICE-001/approve",
            json={"admin_user_id": 1}
        )
        
        # Enroll another (pending)
        second_device = sample_device_enrollment_data.copy()
        second_device["device_id"] = "TEST-DEVICE-002"
        second_device["public_key_hex"] = "b" * 64
        client.post("/api/v1/security/enroll", json=second_device)
        
        # Filter by ACTIVE
        response = client.get("/api/v1/security/enrollments?status=active")
        assert response.status_code == 200
        devices = response.json()
        assert len(devices) == 1
        assert devices[0]["status"] == "active"
    
    def test_enrollment_stats(self, client, sample_device_enrollment_data):
        """Test enrollment statistics endpoint."""
        # Enroll devices
        client.post("/api/v1/security/enroll", json=sample_device_enrollment_data)
        
        # Get stats
        stats_response = client.get("/api/v1/security/enrollments/stats")
        
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert "by_status" in stats
        assert "total" in stats
        assert stats["total"] >= 1
