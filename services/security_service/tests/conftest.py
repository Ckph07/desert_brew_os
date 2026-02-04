"""
Pytest configuration and shared fixtures for Security Service tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app
from fastapi.testclient import TestClient

# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///./test_security.db"


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
    """Create FastAPI test client with overridden dependencies."""
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
def sample_device_enrollment_data():
    """Sample device enrollment request data."""
    return {
        "device_id": "TEST-DEVICE-001",
        "device_model": "iPhone 14 Pro",
        "os_version": "iOS 17.2",
        "public_key_hex": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
        "user_id": 5,
        "user_name": "Juan Vendedor"
    }


@pytest.fixture
def ed25519_keypair():
    """Generate Ed25519 keypair for testing."""
    from nacl.signing import SigningKey
    signing_key = SigningKey.generate()
    return {
        "signing_key": signing_key,
        "verify_key": signing_key.verify_key,
        "public_key_hex": signing_key.verify_key.encode().hex(),
        "private_key_hex": bytes(signing_key).hex()
    }
