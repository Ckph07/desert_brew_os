"""
Pytest configuration for Production Service tests.

Provides mock overrides for external services (Inventory, Finance, RabbitMQ)
so tests run locally without external dependencies.
"""
import os
import pytest
from unittest.mock import MagicMock, AsyncMock

os.environ["DATABASE_URL"] = "sqlite:///./test_production.db"

import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test_production.db"

database.engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)

from database import Base
from main import app
from fastapi.testclient import TestClient


# === Mock External Services ===

class MockEventPublisher:
    """Mock RabbitMQ publisher — no-op for tests."""
    def connect(self): pass
    def publish(self, routing_key, message, exchange="production"): pass
    def close(self): pass


class MockInventoryServiceClient:
    """Mock Inventory Service client for tests."""

    async def get_available_stock_batches(self, ingredient_name, min_quantity=0.01):
        """Return fake stock batches for FIFO allocation."""
        return [
            {
                "id": 1,
                "batch_number": f"MOCK-{ingredient_name[:4].upper()}-001",
                "sku": ingredient_name,
                "available_quantity": 100.0,
                "unit_cost": 25.00,
                "unit_measure": "KG",
                "supplier_name": "Test Supplier",
            }
        ]

    async def consume_stock(self, stock_batch_id, quantity, unit, production_batch_id, reason=None):
        """Mock stock consumption — always succeeds."""
        return {
            "status": "consumed",
            "batch_id": stock_batch_id,
            "quantity_consumed": quantity,
            "remaining_quantity": 100.0 - quantity,
        }

    async def create_finished_product(self, production_batch_id, sku, volume_liters, unit_cost, container_type=None, location=None):
        """Mock finished product creation."""
        return {
            "id": 999,
            "production_batch_id": production_batch_id,
            "sku": sku,
            "volume_liters": volume_liters,
            "unit_cost": unit_cost,
        }

    async def health_check(self):
        return True


class MockFinanceServiceClient:
    """Mock Finance Service client for tests."""

    async def create_internal_transfer(self, origin_type, volume_liters, unit_cost,
                                       production_batch_id, profit_center_from="factory",
                                       profit_center_to="taproom"):
        return {
            "id": "mock-transfer-001",
            "origin_type": origin_type,
            "volume_liters": volume_liters,
            "unit_cost": unit_cost,
            "transfer_price": unit_cost * 1.15,
        }

    async def health_check(self):
        return True


# === Fixtures ===

@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    from models.recipe import Recipe
    from models.production_batch import ProductionBatch
    from models.batch_ingredient_allocation import BatchIngredientAllocation
    from models.ingredient_price import IngredientPrice
    from models.fixed_monthly_cost import FixedMonthlyCost, ProductionTarget

    Base.metadata.create_all(bind=database.engine)
    yield database.engine
    Base.metadata.drop_all(bind=database.engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create FastAPI test client with mocked external dependencies."""
    from database import get_db
    from events.publisher import get_event_publisher
    from clients.inventory_client import get_inventory_client
    from clients.finance_client import get_finance_client

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_event_publisher():
        return MockEventPublisher()

    def override_inventory_client():
        return MockInventoryServiceClient()

    def override_finance_client():
        return MockFinanceServiceClient()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_event_publisher] = override_event_publisher
    app.dependency_overrides[get_inventory_client] = override_inventory_client
    app.dependency_overrides[get_finance_client] = override_finance_client

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_recipe(db_session):
    """Create sample recipe for testing."""
    from models.recipe import Recipe

    recipe = Recipe(
        name="Test IPA",
        style="American IPA",
        batch_size_liters=20.0,
        fermentables=[
            {"name": "Maris Otter", "amount_kg": 5.0, "color_srm": 3.0, "type": "Grain"}
        ],
        hops=[
            {"name": "Cascade", "amount_g": 50.0, "time_min": 60.0, "use": "Boil", "alpha_acid": 5.5}
        ],
        yeast=[
            {"name": "US-05", "lab": "Fermentis", "product_id": "US-05", "type": "Ale"}
        ],
        expected_og=1.065,
        expected_fg=1.012,
        expected_abv=6.96,
        ibu=65.0,
        brewhouse_efficiency=75.0
    )

    db_session.add(recipe)
    db_session.commit()
    db_session.refresh(recipe)

    return recipe
