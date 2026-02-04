"""
Pytest configuration for Sales Service tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "sqlite:///./test_sales.db"


@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


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
