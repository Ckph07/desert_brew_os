"""
Pytest configuration for Finance Service tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "sqlite:///./test_finance.db"


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
def seeded_pricing_rules(db_session):
    """Seed pricing rules for testing."""
    from models.transfer_pricing_rule import TransferPricingRule, PricingStrategy
    
    rules = [
        TransferPricingRule(
            origin_type="house",
            strategy=PricingStrategy.COST_PLUS.value,
            markup_percentage=15.00,
            rule_name="HOUSE - Factory Margin",
            is_active=True
        ),
        TransferPricingRule(
            origin_type="guest",
            strategy=PricingStrategy.PASSTHROUGH.value,
            markup_percentage=0.00,
            rule_name="GUEST - 3PL",
            is_active=True
        ),
        TransferPricingRule(
            origin_type="commercial",
            strategy=PricingStrategy.PASSTHROUGH.value,
            markup_percentage=0.00,
            rule_name="COMMERCIAL - Logistics",
            is_active=True
        ),
        TransferPricingRule(
            origin_type="merchandise",
            strategy=PricingStrategy.FIXED_MARKUP.value,
            markup_percentage=25.00,
            rule_name="MERCHANDISE - Retail",
            is_active=True
        ),
    ]
    
    db_session.add_all(rules)
    db_session.commit()
    
    return rules
