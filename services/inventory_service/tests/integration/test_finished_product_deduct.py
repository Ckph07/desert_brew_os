"""
Contract test for finished product deduction (Sales -> Inventory).
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
import pytest
import os
from main import app
from database import get_db
from models.finished_product import FinishedProductInventory
from models.product_movement import ProductMovement

TEST_DB_URL = "sqlite:///./test_finished_product_deduct.db"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    FinishedProductInventory.__table__.create(bind=test_engine, checkfirst=True)
    ProductMovement.__table__.create(bind=test_engine, checkfirst=True)
    yield
    ProductMovement.__table__.drop(bind=test_engine, checkfirst=True)
    FinishedProductInventory.__table__.drop(bind=test_engine, checkfirst=True)
    if os.path.exists("test_finished_product_deduct.db"):
        os.remove("test_finished_product_deduct.db")


def test_deduct_finished_product_creates_sale_movement_and_updates_qty():
    FinishedProductInventory.__table__.create(bind=test_engine, checkfirst=True)
    ProductMovement.__table__.create(bind=test_engine, checkfirst=True)

    # Create finished product
    create_payload = {
        "sku": "BEER-IPA-KEG",
        "product_name": "IPA Keg",
        "product_type": "OWN_PRODUCTION",
        "category": "BEER_KEG",
        "production_batch_id": 1,
        "quantity": 10,
        "unit_measure": "KEGS",
        "cold_room_id": "COLD_ROOM_A",
        "unit_cost": 50.0,
    }

    create_resp = client.post("/api/v1/inventory/finished-products", json=create_payload)
    assert create_resp.status_code == 201
    product_id = create_resp.json()["id"]

    # Deduct
    deduct_payload = {
        "quantity": 2,
        "movement_reason": "Venta nota 0001",
        "reference_number": "NOTE-0001",
        "user_id": 99,
    }
    deduct_resp = client.post(f"/api/v1/inventory/finished-products/{product_id}/deduct", json=deduct_payload)
    assert deduct_resp.status_code == 200
    data = deduct_resp.json()

    assert Decimal(data["quantity"]) == Decimal("8")
    assert data["availability_status"] == "AVAILABLE"
