"""
Pytest configuration for Production Service tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "sqlite:///./test_production.db"


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
