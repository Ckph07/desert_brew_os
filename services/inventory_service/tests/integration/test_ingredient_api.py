"""
Integration tests for ingredient catalog API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app


TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
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
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


class TestIngredientCatalogApi:
    def test_create_and_list_ingredients(self):
        create_response = client.post(
            "/api/v1/inventory/ingredients",
            json={
                "name": "Malta Pale 2 Row",
                "category": "MALT",
                "unit_measure": "KG",
            },
        )

        assert create_response.status_code == 201
        created = create_response.json()
        assert created["name"] == "Malta Pale 2 Row"
        assert created["category"] == "MALT"
        assert created["unit_measure"] == "KG"
        assert created["sku"] == "MALTA-PALE-2-ROW"
        assert created["is_active"] is True

        list_response = client.get("/api/v1/inventory/ingredients")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data) == 1
        assert data[0]["sku"] == "MALTA-PALE-2-ROW"

    def test_update_ingredient(self):
        create_response = client.post(
            "/api/v1/inventory/ingredients",
            json={
                "name": "Lupulo Cascade",
                "sku": "HOPS-CASCADE",
                "category": "HOPS",
                "unit_measure": "KG",
            },
        )
        ingredient_id = create_response.json()["id"]

        update_response = client.patch(
            f"/api/v1/inventory/ingredients/{ingredient_id}",
            json={
                "name": "Lupulo Cascade Pellet",
                "unit_measure": "G",
                "notes": "Ajuste de presentacion",
            },
        )

        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Lupulo Cascade Pellet"
        assert updated["unit_measure"] == "G"
        assert updated["notes"] == "Ajuste de presentacion"

    def test_deactivate_ingredient(self):
        create_response = client.post(
            "/api/v1/inventory/ingredients",
            json={
                "name": "Levadura US-05",
                "category": "YEAST",
                "unit_measure": "KG",
            },
        )
        ingredient_id = create_response.json()["id"]

        delete_response = client.delete(
            f"/api/v1/inventory/ingredients/{ingredient_id}",
        )
        assert delete_response.status_code == 200

        list_response = client.get("/api/v1/inventory/ingredients?active_only=true")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 0
