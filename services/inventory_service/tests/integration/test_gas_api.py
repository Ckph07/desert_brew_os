"""
Integration tests for gas tank API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from main import app
from database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.supplier import Supplier


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


@pytest.fixture
def test_supplier():
    """Create a test supplier for gas tanks."""
    db = next(override_get_db())
    supplier = Supplier(name="Praxair", rfc="PRA123")
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier.id


class TestGasTankAPI:
    """Tests for gas tank management endpoints."""
    
    def test_register_co2_tank(self, test_supplier):
        """Should register new CO2 tank."""
        response = client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-TANK-001",
            "sku": "CO2-FOOD-25KG",
            "capacity_kg": 25.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "deposit_amount": 500.00,
            "location": "Production Floor"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["tank_code"] == "CO2-TANK-001"
        assert data["sku"] == "CO2-FOOD-25KG"
        assert data["is_full"] == True
        assert data["remaining_percentage"] == 100.0
    
    def test_register_duplicate_tank_code_fails(self, test_supplier):
        """Should not allow duplicate tank codes."""
        # Create first tank
        client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-TANK-DUP",
            "sku": "CO2-FOOD-10KG",
            "capacity_kg": 10.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "location": "Storage"
        })
        
        # Try to create duplicate
        response = client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-TANK-DUP",
            "sku": "CO2-FOOD-10KG",
            "capacity_kg": 10.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "location": "Storage"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_list_gas_tanks(self, test_supplier):
        """Should list all gas tanks."""
        # Create tanks
        client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-001",
            "sku": "CO2-FOOD-25KG",
            "capacity_kg": 25.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "location": "Production"
        })
        
        client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "O2-001",
            "sku": "O2-1M3",
            "capacity_m3": 1.0,
            "ownership_type": "DEPOSIT",
            "supplier_id": test_supplier,
            "location": "Storage"
        })
        
        # List
        response = client.get("/api/v1/inventory/gas-tanks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_consume_gas(self, test_supplier):
        """Should consume gas from tank."""
        # Create tank
        client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-CONSUME",
            "sku": "CO2-FOOD-25KG",
            "capacity_kg": 25.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "location": "Production"
        })
        
        # Consume
        response = client.post("/api/v1/inventory/gas-tanks/consume", json={
            "tank_code": "CO2-CONSUME",
            "quantity_kg": 5.0,
            "production_batch_id": 42,
            "purpose": "CARBONATION",
            "notes": "Test consumption"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["quantity_consumed_kg"] == "5.00"
        assert data["purpose"] == "CARBONATION"
        
        # Verify tank updated
        tank_resp = client.get("/api/v1/inventory/gas-tanks/CO2-CONSUME")
        tank = tank_resp.json()
        assert tank["current_weight_kg"] == "20.00"  # 25 - 5
        assert tank["status"] == "IN_USE"
    
    def test_consume_more_than_available_fails(self, test_supplier):
        """Should not allow consuming more than available."""
        # Create small tank
        client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-SMALL",
            "sku": "CO2-FOOD-10KG",
            "capacity_kg": 10.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "location": "Production"
        })
        
        # Try to consume too much
        response = client.post("/api/v1/inventory/gas-tanks/consume", json={
            "tank_code": "CO2-SMALL",
            "quantity_kg": 15.0,
            "purpose": "CARBONATION"
        })
        
        assert response.status_code == 400
        assert "Cannot consume" in response.json()["detail"]
    
    def test_refill_tank(self, test_supplier):
        """Should refill tank to full capacity."""
        # Create and consume
        client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-REFILL",
            "sku": "CO2-FOOD-25KG",
            "capacity_kg": 25.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "location": "Production"
        })
        
        client.post("/api/v1/inventory/gas-tanks/consume", json={
            "tank_code": "CO2-REFILL",
            "quantity_kg": 20.0,
            "purpose": "CARBONATION"
        })
        
        # Refill
        response = client.post("/api/v1/inventory/gas-tanks/CO2-REFILL/refill")
        assert response.status_code == 200
        
        # Verify full
        tank_resp = client.get("/api/v1/inventory/gas-tanks/CO2-REFILL")
        tank = tank_resp.json()
        assert tank["is_full"] == True
        assert tank["current_weight_kg"] == "25.00"
    
    def test_return_tank_to_supplier(self, test_supplier):
        """Should allow returning nearly empty tank."""
        # Create and consume almost all
        client.post("/api/v1/inventory/gas-tanks", json={
            "tank_code": "CO2-RETURN",
            "sku": "CO2-FOOD-10KG",
            "capacity_kg": 10.0,
            "ownership_type": "RENTED",
            "supplier_id": test_supplier,
            "deposit_amount": 500.0,
            "location": "Production"
        })
        
        client.post("/api/v1/inventory/gas-tanks/consume", json={
            "tank_code": "CO2-RETURN",
            "quantity_kg": 9.5,  # Leave only 0.5kg (5%)
            "purpose": "PUSHING"
        })
        
        # Return
        response = client.post("/api/v1/inventory/gas-tanks/CO2-RETURN/return")
        
        assert response.status_code == 200
        assert response.json()["deposit_amount"] == 500.0
        
        # Verify location changed
        tank_resp = client.get("/api/v1/inventory/gas-tanks/CO2-RETURN")
        assert tank_resp.json()["location"] == "With Supplier"
