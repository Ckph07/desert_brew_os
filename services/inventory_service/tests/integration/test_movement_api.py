"""
Integration tests for transfer and movement API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from datetime import datetime, timedelta
from main import app
from database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.stock import StockBatch
from models.movement import StockMovement
from models.transfer import StockTransfer


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


class TestTransferAPI:
    """Tests for POST /api/v1/inventory/transfer endpoint."""
    
    def test_transfer_endpoint_success(self):
        """Should successfully transfer stock via API."""
        # Arrange: Create stock
        db = next(override_get_db())
        batch = StockBatch(
            sku="MALT-PALE-2ROW",
            batch_number="LOT-001",
            category="MALT",
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("100"),
            unit_measure="KG",
            unit_cost=Decimal("18"),
            total_cost=Decimal("1800"),
            location="Silo A"
        )
        db.add(batch)
        db.commit()
        
        # Act: Transfer via API
        response = client.post("/api/v1/inventory/transfer", json={
            "sku": "MALT-PALE-2ROW",
            "quantity": 50.0,
            "from_location": "Silo A",
            "to_location": "Silo B",
            "notes": "Test transfer"
        }, params={"requested_by": "test_user"})
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "MALT-PALE-2ROW"
        assert data["quantity"] == "50.000"
        assert data["from_location"] == "Silo A"
        assert data["to_location"] == "Silo B"
        assert data["status"] == "COMPLETED"
        assert data["requested_by"] == "test_user"
    
    def test_transfer_endpoint_insufficient_stock(self):
        """Should return 400 if insufficient stock."""
        # Arrange: Only 10kg available
        db = next(override_get_db())
        batch = StockBatch(
            sku="HOPS-CASCADE",
            category="HOPS",
            initial_quantity=Decimal("10"),
            remaining_quantity=Decimal("10"),
            unit_measure="G",
            unit_cost=Decimal("120"),
            total_cost=Decimal("1200"),
            location="Warehouse"
        )
        db.add(batch)
        db.commit()
        
        # Act: Try to transfer 20g
        response = client.post("/api/v1/inventory/transfer", json={
            "sku": "HOPS-CASCADE",
            "quantity": 20.0,
            "from_location": "Warehouse",
            "to_location": "Taproom"
        })
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "insufficient_stock"
        assert data["detail"]["requested"] == 20.0
        assert data["detail"]["available"] == 10.0


class TestTransferListAPI:
    """Tests for GET /api/v1/inventory/transfers endpoint."""
    
    def test_list_transfers(self):
        """Should list all transfers."""
        # Arrange: Create transfers
        db = next(override_get_db())
        transfer1 = StockTransfer(
            sku="MALT-PALE-2ROW",
            quantity=Decimal("50"),
            unit_measure="KG",
            from_location="Silo A",
            to_location="Silo B",
            status="COMPLETED"
        )
        transfer2 = StockTransfer(
            sku="HOPS-CASCADE",
            quantity=Decimal("100"),
            unit_measure="G",
            from_location="Warehouse",
            to_location="Taproom",
            status="PENDING"
        )
        db.add_all([transfer1, transfer2])
        db.commit()
        
        # Act
        response = client.get("/api/v1/inventory/transfers")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_list_transfers_filter_by_sku(self):
        """Should filter transfers by SKU."""
        # Arrange
        db = next(override_get_db())
        transfer1 = StockTransfer(
            sku="MALT-PALE-2ROW",
            quantity=Decimal("50"),
            unit_measure="KG",
            from_location="Silo A",
            to_location="Silo B",
            status="COMPLETED"
        )
        transfer2 = StockTransfer(
            sku="HOPS-CASCADE",
            quantity=Decimal("100"),
            unit_measure="G",
            from_location="Warehouse",
            to_location="Taproom",
            status="COMPLETED"
        )
        db.add_all([transfer1, transfer2])
        db.commit()
        
        # Act: Filter by MALT
        response = client.get("/api/v1/inventory/transfers?sku=MALT-PALE-2ROW")
        
        # Assert: Only MALT transfer
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sku"] == "MALT-PALE-2ROW"


class TestMovementHistoryAPI:
    """Tests for GET /api/v1/inventory/movements endpoint."""
    
    def test_list_movements(self):
        """Should list movement history."""
        # Arrange: Create movements
        db = next(override_get_db())
        mov1 = StockMovement(
            batch_id=1,
            sku="MALT-PALE-2ROW",
            movement_type="CONSUMPTION",
            quantity=Decimal("50"),
            unit_measure="KG",
            reference="Production Order #1"
        )
        mov2 = StockMovement(
            batch_id=2,
            sku="HOPS-CASCADE",
            movement_type="WASTE",
            quantity=Decimal("5"),
            unit_measure="G",
            reference="Quality Issue"
        )
        db.add_all([mov1, mov2])
        db.commit()
        
        # Act
        response = client.get("/api/v1/inventory/movements")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_movements_filter_by_type(self):
        """Should filter movements by type."""
        # Arrange
        db = next(override_get_db())
        consumption = StockMovement(
            batch_id=1,
            sku="MALT-PALE-2ROW",
            movement_type="CONSUMPTION",
            quantity=Decimal("50"),
            unit_measure="KG"
        )
        waste = StockMovement(
            batch_id=2,
            sku="HOPS-CASCADE",
            movement_type="WASTE",
            quantity=Decimal("5"),
            unit_measure="G"
        )
        db.add_all([consumption, waste])
        db.commit()
        
        # Act: Filter WASTE only
        response = client.get("/api/v1/inventory/movements?movement_type=WASTE")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["movement_type"] == "WASTE"
    
    def test_movement_summary_by_sku(self):
        """Should aggregate movements by type."""
        # Arrange: Multiple movements of same SKU
        db = next(override_get_db())
        movements = [
            StockMovement(
                sku="MALT-PALE-2ROW",
                movement_type="CONSUMPTION",
                quantity=Decimal("50"),
                unit_measure="KG"
            ),
            StockMovement(
                sku="MALT-PALE-2ROW",
                movement_type="CONSUMPTION",
                quantity=Decimal("30"),
                unit_measure="KG"
            ),
            StockMovement(
                sku="MALT-PALE-2ROW",
                movement_type="WASTE",
                quantity=Decimal("5"),
                unit_measure="KG"
            ),
        ]
        db.add_all(movements)
        db.commit()
        
        # Act
        response = client.get("/api/v1/inventory/movements/MALT-PALE-2ROW/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Find consumption summary
        consumption = next(d for d in data if d["movement_type"] == "CONSUMPTION")
        assert consumption["total_quantity"] == 80.0  # 50 + 30
        assert consumption["total_movements"] == 2
        
        # Find waste summary
        waste = next(d for d in data if d["movement_type"] == "WASTE")
        assert waste["total_quantity"] == 5.0
        assert waste["total_movements"] == 1
