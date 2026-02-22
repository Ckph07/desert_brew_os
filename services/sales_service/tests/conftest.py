"""
Pytest configuration for Sales Service tests.

Updated for Sprint 5.5: Includes all new models.
Patches database engine before importing main to avoid psycopg2 requirement.
"""
import os
import pytest

# Set test database URL BEFORE any other imports
os.environ["DATABASE_URL"] = "sqlite:///./test_sales.db"

# Now patch database module to use SQLite before main is imported
import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test_sales.db"

database.engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)

from database import Base
from main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    # Import all models so they are registered with Base
    from models.commission_tier import CommissionTier
    from models.client import Client
    from models.product_catalog import ProductCatalog
    from models.price_history import PriceHistory
    from models.sales_note import SalesNote, SalesNoteItem

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
    """Create FastAPI test client."""
    from database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_tiers(db_session):
    """Seed commission tiers for testing."""
    from models.commission_tier import CommissionTier

    tiers = [
        CommissionTier(
            name="Platinum",
            min_monthly_liters=500.0,
            commission_rate_per_liter=2.50,
            description="Elite sellers >500L/month",
            badge_color="platinum",
            is_active=True
        ),
        CommissionTier(
            name="Gold",
            min_monthly_liters=200.0,
            commission_rate_per_liter=2.00,
            description="High performers 200-499L",
            badge_color="gold",
            is_active=True
        ),
        CommissionTier(
            name="Silver",
            min_monthly_liters=50.0,
            commission_rate_per_liter=1.50,
            description="Standard 50-199L",
            badge_color="silver",
            is_active=True
        ),
        CommissionTier(
            name="Bronze",
            min_monthly_liters=0.0,
            commission_rate_per_liter=1.00,
            description="Entry level <50L",
            badge_color="bronze",
            is_active=True
        ),
    ]

    db_session.add_all(tiers)
    db_session.commit()

    return tiers


@pytest.fixture
def sample_client_data():
    """Sample client creation data."""
    return {
        "business_name": "Bar La Herradura",
        "legal_name": "La Herradura SA de CV",
        "rfc": "HER200101ABC",
        "client_type": "B2B",
        "pricing_tier": "GOLD",
        "email": "contacto@laherradura.mx",
        "phone": "+52 844 123 4567",
        "address": "Blvd. V. Carranza 1234, Saltillo",
        "city": "Saltillo",
        "state": "Coahuila",
        "credit_limit": 50000.00,
        "max_kegs": 10,
    }


@pytest.fixture
def sample_product_data():
    """Sample product creation data with dual pricing."""
    return {
        "sku": "BEER-IPA-COAHUI-L",
        "product_name": "Litro Coahuilaceratops (Imperial Indian Pale Ale)",
        "style": "Imperial IPA",
        "category": "BEER_LITER",
        "origin_type": "HOUSE",
        "unit_measure": "LITROS",
        "abv": 7.2,
        "ibu": 75,
        "fixed_price": 109.44,
        "theoretical_price": 95.00,
        "cost_per_unit": 21.54,
        "price_taproom": 130.00,
        "price_distributor": 109.44,
    }


