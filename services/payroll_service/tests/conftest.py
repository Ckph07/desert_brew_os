"""
Pytest configuration for Payroll Service tests.
"""
import os
import pytest

os.environ["DATABASE_URL"] = "sqlite:///./test_payroll.db"

import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test_payroll.db"

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
    from models.employee import Employee, PayrollEntry, TipPool

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
def sample_brewery_employee():
    """Sample brewery fixed employee."""
    return {
        "full_name": "Miguel Ángel Rodríguez",
        "role": "BREWMASTER",
        "department": "PRODUCTION",
        "employment_type": "FIXED",
        "daily_salary": 833.33,
        "phone": "+52 844 987 6543",
    }


@pytest.fixture
def sample_taproom_employee():
    """Sample taproom fixed employee with tips and taxi."""
    return {
        "full_name": "Laura Martínez",
        "role": "BARTENDER",
        "department": "TAPROOM",
        "employment_type": "FIXED",
        "daily_salary": 500.00,
        "eligible_for_tips": True,
        "taxi_allowance_per_shift": 80.00,
    }


@pytest.fixture
def sample_temp_worker():
    """Sample taproom temp worker."""
    return {
        "full_name": "Carlos Temporal",
        "role": "WAITER",
        "department": "TAPROOM",
        "employment_type": "TEMPORARY",
        "daily_salary": 350.00,
        "eligible_for_tips": True,
        "taxi_allowance_per_shift": 80.00,
    }
