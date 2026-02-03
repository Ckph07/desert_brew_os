"""
Pytest fixtures for Inventory Service tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.stock import StockBatch
from decimal import Decimal
from datetime import datetime, timedelta


# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}  # For SQLite
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_stock_batch():
    """Factory fixture for creating StockBatch instances."""
    def _create_batch(
        sku="MALT-PALE-2ROW",
        quantity=100.0,
        arrival_date=None,
        batch_number="LOT-TEST-001",
        unit_cost=18.50
    ):
        return StockBatch(
            sku=sku,
            batch_number=batch_number,
            category="MALT",
            arrival_date=arrival_date or datetime.utcnow(),
            initial_quantity=Decimal(str(quantity)),
            remaining_quantity=Decimal(str(quantity)),
            unit_measure="KG",
            unit_cost=Decimal(str(unit_cost)),
            total_cost=Decimal(str(quantity * unit_cost)),
            provider_name="Test Provider"
        )
    return _create_batch
