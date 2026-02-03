"""
Integration tests for Inventory Service API.

Tests full request/response cycle with database.
"""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime, timedelta
from main import app
from database import get_db, Base, engine as prod_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.stock import StockBatch


# Test database
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


# Override dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown test database for each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


class TestStockReceiptAPI:
    """Tests for POST /api/v1/inventory/stock endpoint."""
    
    def test_receive_new_stock_success(self):
        """Debe crear un nuevo lote correctamente."""
        # Arrange
        payload = {
            "sku": "MALT-PALE-2ROW",
            "batch_number": "LOT-2026-005",
            "category": "MALT",
            "quantity": 250.0,
            "unit_measure": "KG",
            "unit_cost": 18.50,
            "provider_name": "Malterías Tepeyac",
            "location": "Silo A"
        }
        
        # Act
        response = client.post("/api/v1/inventory/stock", json=payload)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "MALT-PALE-2ROW"
        assert data["remaining_quantity"] == "250.000"
        assert data["initial_quantity"] == "250.000"
        assert data["total_cost"] == "4625.00"  # 250 * 18.50
        assert data["is_allocated"] == False
    
    def test_sku_converted_to_uppercase(self):
        """SKU debe convertirse a mayúsculas automáticamente."""
        payload = {
            "sku": "hops-cascade",  # lowercase
            "category": "HOPS",
            "quantity": 100.0,
            "unit_measure": "G",
            "unit_cost": 120.00
        }
        
        response = client.post("/api/v1/inventory/stock", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "HOPS-CASCADE"  # Uppercase
    
    def test_validation_rejects_zero_quantity(self):
        """Debe rechazar cantidad cero o negativa."""
        payload = {
            "sku": "MALT-PALE-2ROW",
            "category": "MALT",
            "quantity": 0,  # Invalid
            "unit_measure": "KG",
            "unit_cost": 18.50
        }
        
        response = client.post("/api/v1/inventory/stock", json=payload)
        assert response.status_code == 422  # Validation error


class TestStockQueryAPI:
    """Tests for GET endpoints."""
    
    def test_get_stock_by_sku(self):
        """Debe retornar lotes de un SKU específico."""
        # Arrange: Create stock first
        db = next(override_get_db())
        batch1 = StockBatch(
            sku="HOPS-SIMCOE",
            batch_number="LOT-1",
            category="HOPS",
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("100"),
            unit_measure="G",
            unit_cost=Decimal("150"),
            total_cost=Decimal("15000")
        )
        batch2 = StockBatch(
            sku="HOPS-SIMCOE",
            batch_number="LOT-2",
            category="HOPS",
            initial_quantity=Decimal("50"),
            remaining_quantity=Decimal("50"),
            unit_measure="G",
            unit_cost=Decimal("150"),
            total_cost=Decimal("7500")
        )
        db.add_all([batch1, batch2])
        db.commit()
        
        # Act
        response = client.get("/api/v1/inventory/stock/HOPS-SIMCOE")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(item["sku"] == "HOPS-SIMCOE" for item in data)
    
    def test_get_nonexistent_sku_returns_404(self):
        """Debe retornar 404 si el SKU no existe."""
        response = client.get("/api/v1/inventory/stock/NONEXISTENT-SKU")
        assert response.status_code == 404
    
    def test_list_stock_with_category_filter(self):
        """Debe filtrar por categoría correctamente."""
        # Arrange
        db = next(override_get_db())
        malt = StockBatch(
            sku="MALT-MUNICH",
            category="MALT",
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("100"),
            unit_measure="KG",
            unit_cost=Decimal("20"),
            total_cost=Decimal("2000")
        )
        hops = StockBatch(
            sku="HOPS-CASCADE",
            category="HOPS",
            initial_quantity=Decimal("50"),
            remaining_quantity=Decimal("50"),
            unit_measure="G",
            unit_cost=Decimal("120"),
            total_cost=Decimal("6000")
        )
        db.add_all([malt, hops])
        db.commit()
        
        # Act
        response = client.get("/api/v1/inventory/stock?category=MALT")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "MALT"


class TestFIFOAllocationAPI:
    """Tests for POST /api/v1/inventory/allocate endpoint."""
    
    def test_allocate_stock_success(self):
        """Debe asignar stock usando FIFO correctamente."""
        # Arrange: Create batches
        db = next(override_get_db())
        old_batch = StockBatch(
            sku="MALT-PALE-2ROW",
            batch_number="OLD",
            category="MALT",
            arrival_date=datetime.utcnow() - timedelta(days=5),
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("100"),
            unit_measure="KG",
            unit_cost=Decimal("18"),
            total_cost=Decimal("1800")
        )
        new_batch = StockBatch(
            sku="MALT-PALE-2ROW",
            batch_number="NEW",
            category="MALT",
            arrival_date=datetime.utcnow(),
            initial_quantity=Decimal("50"),
            remaining_quantity=Decimal("50"),
            unit_measure="KG",
            unit_cost=Decimal("20"),
            total_cost=Decimal("1000")
        )
        db.add_all([old_batch, new_batch])
        db.commit()
        
        # Act: Allocate 80kg
        response = client.post("/api/v1/inventory/allocate", json={
            "sku": "MALT-PALE-2ROW",
            "amount_needed": 80
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "MALT-PALE-2ROW"
        assert data["total_allocated"] == "80.000"
        assert len(data["allocations"]) == 1
        assert data["allocations"][0]["batch_number"] == "OLD"
    
    def test_allocate_insufficient_stock_returns_400(self):
        """Debe retornar error 400 si no hay suficiente stock."""
        # Arrange: Only 10kg available
        db = next(override_get_db())
        batch = StockBatch(
            sku="YEAST-US05",
            category="YEAST",
            initial_quantity=Decimal("10"),
            remaining_quantity=Decimal("10"),
            unit_measure="G",
            unit_cost=Decimal("50"),
            total_cost=Decimal("500")
        )
        db.add(batch)
        db.commit()
        
        # Act: Try to allocate 20g
        response = client.post("/api/v1/inventory/allocate", json={
            "sku": "YEAST-US05",
            "amount_needed": 20
        })
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "insufficient_stock"
        assert data["detail"]["sku"] == "YEAST-US05"
        assert data["detail"]["requested"] == 20.0
        assert data["detail"]["available"] == 10.0


class TestInventorySummary:
    """Tests for GET /api/v1/inventory/summary endpoint."""
    
    def test_summary_aggregates_by_category(self):
        """Debe agregar correctamente por categoría."""
        # Arrange
        db = next(override_get_db())
        malt1 = StockBatch(
            sku="MALT-PALE",
            category="MALT",
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("80"),
            unit_measure="KG",
            unit_cost=Decimal("18"),
            total_cost=Decimal("1800")
        )
        malt2 = StockBatch(
            sku="MALT-MUNICH",
            category="MALT",
            initial_quantity=Decimal("50"),
            remaining_quantity=Decimal("50"),
            unit_measure="KG",
            unit_cost=Decimal("20"),
            total_cost=Decimal("1000")
        )
        hops = StockBatch(
            sku="HOPS-CASCADE",
            category="HOPS",
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("100"),
            unit_measure="G",
            unit_cost=Decimal("120"),
            total_cost=Decimal("12000")
        )
        db.add_all([malt1, malt2, hops])
        db.commit()
        
        # Act
        response = client.get("/api/v1/inventory/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Should have 2 categories
        assert len(data) == 2
        
        # Find MALT category
        malt_summary = next(c for c in data if c["category"] == "MALT")
        assert malt_summary["total_batches"] == 2
        assert malt_summary["total_quantity"] == 130.0  # 80 + 50
