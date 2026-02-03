"""
Integration tests for Keg API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from models.keg_enums import KegState
import uuid


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_kegs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestKegCRUD:
    """Tests for basic CRUD operations."""
    
    def test_create_keg_success(self):
        """Test creating a new keg."""
        response = client.post(
            "/api/v1/inventory/kegs",
            json={
                "serial_number": "KEG-2026-001",
                "size_liters": 30,
                "keg_type": "SANKE_D"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["serial_number"] == "KEG-2026-001"
        assert data["size_liters"] == 30
        assert data["current_state"] == "EMPTY"
        assert "qr_code" in data  # Auto-generated
        assert data["qr_code"].startswith("KEG-KEG-2026-001-")
    
    def test_create_keg_duplicate_serial(self):
        """Test creating keg with duplicate serial fails."""
        # Create first keg
        client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-DUP-001", "size_liters": 30}
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-DUP-001", "size_liters": 30}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_list_kegs(self):
        """Test listing kegs."""
        # Create multiple kegs
        for i in range(3):
            client.post(
                "/api/v1/inventory/kegs",
                json={
                    "serial_number": f"KEG-LIST-{i:03d}",
                    "size_liters": 30
                }
            )
        
        response = client.get("/api/v1/inventory/kegs")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_list_kegs_with_state_filter(self):
        """Test filtering kegs by state."""
        # Create kegs and transition one to CLEAN
        keg1_resp = client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-FILTER-001", "size_liters": 30}
        )
        keg1_id = keg1_resp.json()["id"]
        
        client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-FILTER-002", "size_liters": 30}
        )
        
        # Transition keg1 to CLEAN
        client.patch(
            f"/api/v1/inventory/kegs/{keg1_id}/transition",
            json={
                "new_state": "CLEAN",
                "user_id": 1
            }
        )
        
        # Filter by CLEAN
        response = client.get("/api/v1/inventory/kegs", params={"state": "CLEAN"})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["current_state"] == "CLEAN"
    
    def test_get_keg_with_history(self):
        """Test getting keg with transition history."""
        # Create keg
        keg_resp = client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-HISTORY-001", "size_liters": 30}
        )
        keg_id = keg_resp.json()["id"]
        
        # Make some transitions
        client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={"new_state": "DIRTY", "user_id": 1}
        )
        client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={"new_state": "CLEAN", "user_id": 1}
        )
        
        # Get keg with history
        response = client.get(f"/api/v1/inventory/kegs/{keg_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["transitions"]) >= 2


class TestKegTransitions:
    """Tests for state transitions."""
    
    def test_transition_empty_to_clean(self):
        """Test valid transition: EMPTY → CLEAN."""
        # Create keg
        keg_resp = client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-TRANS-001", "size_liters": 30}
        )
        keg_id = keg_resp.json()["id"]
        
        # Transition to CLEAN
        response = client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={
                "new_state": "CLEAN",
                "user_id": 5,
                "location": "Washing Station"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["from_state"] == "EMPTY"
        assert data["to_state"] == "CLEAN"
        assert data["user_id"] == 5
        
        # Verify keg state updated
        keg = client.get(f"/api/v1/inventory/kegs/{keg_id}").json()
        assert keg["current_state"] == "CLEAN"
        assert keg["last_cleaned_at"] is not None
    
    def test_transition_invalid_empty_to_full(self):
        """Test invalid transition: EMPTY → FULL (skipping CLEAN)."""
        # Create keg
        keg_resp = client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-INVALID-001", "size_liters": 30}
        )
        keg_id = keg_resp.json()["id"]
        
        # Try invalid transition
        response = client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={
                "new_state": "FULL",
                "user_id": 5,
                "batch_id": 42
            }
        )
        
        assert response.status_code == 400
        assert "Cannot transition" in response.json()["detail"]
    
    def test_transition_full_requires_batch_id(self):
        """Test FULL state requires batch_id."""
        # Create keg and get to FILLING state
        keg_resp = client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-BATCH-001", "size_liters": 30}
        )
        keg_id = keg_resp.json()["id"]
        
        client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={"new_state": "CLEAN", "user_id": 5}
        )
        client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={"new_state": "FILLING", "user_id": 5}
        )
        
        # Try FULL without batch_id
        response = client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={"new_state": "FULL", "user_id": 5}
        )
        
        assert response.status_code == 400
        assert "batch_id required" in response.json()["detail"]


class TestKegBulkOperations:
    """Tests for bulk scanning and filling."""
    
    def test_bulk_scan_qr_codes_success(self):
        """Test bulk QR code scanning."""
        # Create 3 kegs
        qr_codes = []
        for i in range(3):
            resp = client.post(
                "/api/v1/inventory/kegs",
                json={"serial_number": f"KEG-BULK-{i:03d}", "size_liters": 30}
            )
            qr_codes.append(resp.json()["qr_code"])
        
        # Bulk transition to CLEAN
        response = client.post(
            "/api/v1/inventory/kegs/bulk-scan",
            json={
                "qr_codes": qr_codes,
                "new_state": "CLEAN",
                "location": "Washing Station",
                "user_id": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["failed_count"] == 0
    
    def test_bulk_scan_invalid_qr_code(self):
        """Test bulk scan with non-existent QR code."""
        response = client.post(
            "/api/v1/inventory/kegs/bulk-scan",
            json={
                "qr_codes": ["INVALID-QR-123"],
                "new_state": "CLEAN",
                "location": "Test",
                "user_id": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["failed_count"] == 1
        assert "not found" in data["errors"][0]
    
    def test_fill_batch_success(self):
        """Test filling multiple kegs from batch."""
        # Create and clean 3 kegs
        keg_ids = []
        for i in range(3):
            resp = client.post(
                "/api/v1/inventory/kegs",
                json={"serial_number": f"KEG-FILL-{i:03d}", "size_liters": 30}
            )
            keg_id = resp.json()["id"]
            keg_ids.append(keg_id)
            
            # Clean keg
            client.patch(
                f"/api/v1/inventory/kegs/{keg_id}/transition",
                json={"new_state": "CLEAN", "user_id": 5}
            )
        
        # Fill all with batch
        response = client.post(
            "/api/v1/inventory/kegs/fill-batch",
            json={
                "batch_id": 42,
                "keg_ids": keg_ids,
                "filled_by": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        
        # Verify kegs are FULL with batch_id
        for keg_id in keg_ids:
            keg = client.get(f"/api/v1/inventory/kegs/{keg_id}").json()
            assert keg["current_state"] == "FULL"
            assert keg["production_batch_id"] == 42
            assert keg["cycle_count"] == 1
    
    def test_fill_batch_dirty_keg_fails(self):
        """Test filling fails if keg is DIRTY."""
        # Create DIRTY keg
        resp = client.post(
            "/api/v1/inventory/kegs",
            json={"serial_number": "KEG-DIRTY", "size_liters": 30}
        )
        keg_id = resp.json()["id"]
        
        client.patch(
            f"/api/v1/inventory/kegs/{keg_id}/transition",
            json={"new_state": "DIRTY", "user_id": 5}
        )
        
        # Try to fill
        response = client.post(
            "/api/v1/inventory/kegs/fill-batch",
            json={
                "batch_id": 42,
                "keg_ids": [keg_id],
                "filled_by": 5
            }
        )
        
        assert response.status_code == 400
        assert "must be CLEAN" in response.json()["detail"]


class TestKegAtRisk:
    """Tests for at-risk kegs report."""
    
    def test_kegs_at_risk_empty_list(self):
        """Test at-risk report when no kegs in client."""
        response = client.get("/api/v1/inventory/kegs/at-risk")
        
        assert response.status_code == 200
        assert response.json() == []


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
