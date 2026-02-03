"""
Integration tests for supplier API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Test database setup
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


class TestSupplierAPI:
    """Tests for supplier CRUD endpoints."""
    
    def test_create_supplier(self):
        """Should create supplier via POST /suppliers."""
        response = client.post("/api/v1/suppliers", json={
            "name": "Malterías Tepeyac",
            "legal_name": "Malterías Tepeyac S.A. de C.V.",
            "rfc": "MTE850101ABC",
            "email": "ventas@tepeyac.com.mx",
            "phone": "+52 81 8888 9999",
            "payment_terms": "30 días",
            "preferred": True
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Malterías Tepeyac"
        assert data["rfc"] == "MTE850101ABC"
        assert data["is_active"] == True
        assert data["preferred"] == True
        assert "id" in data
    
    def test_list_suppliers(self):
        """Should list all suppliers."""
        # Create suppliers
        client.post("/api/v1/suppliers", json={"name": "Supplier A"})
        client.post("/api/v1/suppliers", json={"name": "Supplier B"})
        
        # List
        response = client.get("/api/v1/suppliers")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_list_suppliers_active_only(self):
        """Should filter active suppliers only."""
        # Create active and inactive
        resp1 = client.post("/api/v1/suppliers", json={"name": "Active"})
        supplier_id = resp1.json()["id"]
        
        client.post("/api/v1/suppliers", json={"name": "Inactive"})
        
        # Deactivate first one
        client.delete(f"/api/v1/suppliers/{supplier_id}")
        
        # List active only
        response = client.get("/api/v1/suppliers?active_only=true")
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == "Inactive"
    
    def test_get_supplier_by_id(self):
        """Should get supplier details."""
        # Create
        create_resp = client.post("/api/v1/suppliers", json={
            "name": "Test Supplier",
            "rfc": "TST123"
        })
        supplier_id = create_resp.json()["id"]
        
        # Get
        response = client.get(f"/api/v1/suppliers/{supplier_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Supplier"
        assert data["rfc"] == "TST123"
    
    def test_update_supplier(self):
        """Should update supplier information."""
        # Create
        create_resp = client.post("/api/v1/suppliers", json={"name": "Original"})
        supplier_id = create_resp.json()["id"]
        
        # Update
        response = client.patch(f"/api/v1/suppliers/{supplier_id}", json={
            "name": "Updated Name",
            "quality_rating": 4.5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["quality_rating"] == "4.50"
    
    def test_deactivate_supplier(self):
        """Should deactivate (soft delete) supplier."""
        # Create
        create_resp = client.post("/api/v1/suppliers", json={"name": "To Delete"})
        supplier_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(f"/api/v1/suppliers/{supplier_id}")
        
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"].lower()
        
        # Verify still exists but inactive
        get_resp = client.get(f"/api/v1/suppliers/{supplier_id}")
        assert get_resp.json()["is_active"] == False
    
    def test_supplier_not_found(self):
        """Should return 404 for non-existent supplier."""
        response = client.get("/api/v1/suppliers/99999")
        assert response.status_code == 404
