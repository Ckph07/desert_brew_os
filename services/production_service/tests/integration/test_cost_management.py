"""
Integration tests for Ingredient Price and Fixed Cost Management.
"""
import pytest


class TestIngredientPriceAPI:
    """Test ingredient price CRUD."""

    def test_create_ingredient(self, client):
        """Test creating a malt ingredient."""
        response = client.post("/api/v1/production/ingredients", json={
            "name": "Malta Pale Ale / Pilsen",
            "category": "MALT",
            "unit_measure": "KG",
            "current_price": 25.80,
            "supplier_name": "Malteurop",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Malta Pale Ale / Pilsen"
        assert data["category"] == "MALT"
        assert data["current_price"] == 25.80
        assert data["is_active"] is True

    def test_create_hop(self, client):
        """Test creating a hop ingredient (price per gram)."""
        response = client.post("/api/v1/production/ingredients", json={
            "name": "Cryo Mosaic",
            "category": "HOP",
            "unit_measure": "G",
            "current_price": 2.16,
        })
        assert response.status_code == 201
        assert response.json()["unit_measure"] == "G"

    def test_create_yeast(self, client):
        """Test creating a yeast ingredient."""
        response = client.post("/api/v1/production/ingredients", json={
            "name": "Levadura 34/70",
            "category": "YEAST",
            "unit_measure": "PACKET",
            "current_price": 1892.00,
            "notes": "Ladrillo 500g",
        })
        assert response.status_code == 201
        assert response.json()["current_price"] == 1892.00

    def test_list_ingredients(self, client):
        """Test listing ingredients."""
        # Seed
        client.post("/api/v1/production/ingredients", json={
            "name": "Malta Pale Ale", "category": "MALT",
            "unit_measure": "KG", "current_price": 25.80,
        })
        client.post("/api/v1/production/ingredients", json={
            "name": "Cryo Mosaic", "category": "HOP",
            "unit_measure": "G", "current_price": 2.16,
        })
        response = client.get("/api/v1/production/ingredients")
        assert response.status_code == 200
        assert len(response.json()) >= 2

    def test_filter_by_category(self, client):
        """Test filtering by category."""
        client.post("/api/v1/production/ingredients", json={
            "name": "Malta A", "category": "MALT",
            "unit_measure": "KG", "current_price": 20.00,
        })
        client.post("/api/v1/production/ingredients", json={
            "name": "Hop A", "category": "HOP",
            "unit_measure": "G", "current_price": 1.50,
        })
        response = client.get("/api/v1/production/ingredients?category=MALT")
        assert response.status_code == 200
        assert all(i["category"] == "MALT" for i in response.json())

    def test_search_by_name(self, client):
        """Test search by name."""
        client.post("/api/v1/production/ingredients", json={
            "name": "Viking Cookie Malt", "category": "MALT",
            "unit_measure": "KG", "current_price": 48.10,
        })
        response = client.get("/api/v1/production/ingredients?search=Cookie")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_update_price(self, client):
        """Test updating a price."""
        create = client.post("/api/v1/production/ingredients", json={
            "name": "Malta Test", "category": "MALT",
            "unit_measure": "KG", "current_price": 25.00,
        })
        iid = create.json()["id"]
        response = client.patch(f"/api/v1/production/ingredients/{iid}", json={
            "current_price": 28.50,
        })
        assert response.status_code == 200
        assert response.json()["current_price"] == 28.50

    def test_delete_ingredient(self, client):
        """Test soft-delete."""
        create = client.post("/api/v1/production/ingredients", json={
            "name": "Old Hop", "category": "HOP",
            "unit_measure": "G", "current_price": 1.00,
        })
        iid = create.json()["id"]
        response = client.delete(f"/api/v1/production/ingredients/{iid}")
        assert response.status_code == 204

        # Should not appear in active list
        active = client.get("/api/v1/production/ingredients")
        ids = [i["id"] for i in active.json()]
        assert iid not in ids

    def test_ingredient_summary(self, client):
        """Test ingredient summary by category."""
        client.post("/api/v1/production/ingredients", json={
            "name": "M1", "category": "MALT", "unit_measure": "KG", "current_price": 25.00,
        })
        client.post("/api/v1/production/ingredients", json={
            "name": "M2", "category": "MALT", "unit_measure": "KG", "current_price": 30.00,
        })
        client.post("/api/v1/production/ingredients", json={
            "name": "H1", "category": "HOP", "unit_measure": "G", "current_price": 2.00,
        })
        response = client.get("/api/v1/production/ingredients/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_ingredients"] == 3


class TestFixedCostAPI:
    """Test fixed monthly cost CRUD."""

    DESERT_BREW_COSTS = [
        {"category": "FUEL", "concept": "Gasolina", "monthly_amount": 2000.00},
        {"category": "ENERGY", "concept": "Energía", "monthly_amount": 8000.00},
        {"category": "WATER", "concept": "Agua", "monthly_amount": 2500.00},
        {"category": "HR", "concept": "Recursos Humanos (Salarios + Admon)", "monthly_amount": 25000.00},
        {"category": "OPERATIONS", "concept": "Operación de Planta", "monthly_amount": 9500.00},
        {"category": "GAS_CO2", "concept": "Suministros Gas y CO2", "monthly_amount": 7500.00},
        {"category": "COMMS", "concept": "Comunicaciones (Internet)", "monthly_amount": 900.00},
        {"category": "VEHICLE", "concept": "Fondo Desgaste Vehicular", "monthly_amount": 2500.00},
    ]

    def _seed_costs(self, client):
        """Seed all Desert Brew fixed costs."""
        for cost in self.DESERT_BREW_COSTS:
            client.post("/api/v1/production/costs/fixed", json=cost)

    def test_create_fixed_cost(self, client):
        """Test creating a fixed cost."""
        response = client.post("/api/v1/production/costs/fixed", json={
            "category": "ENERGY",
            "concept": "Energía Eléctrica",
            "monthly_amount": 8000.00,
        })
        assert response.status_code == 201
        assert response.json()["monthly_amount"] == 8000.00

    def test_list_fixed_costs(self, client):
        """Test listing all costs."""
        self._seed_costs(client)
        response = client.get("/api/v1/production/costs/fixed")
        assert response.status_code == 200
        assert len(response.json()) == 8

    def test_update_fixed_cost(self, client):
        """Test updating a cost amount."""
        create = client.post("/api/v1/production/costs/fixed", json={
            "category": "ENERGY", "concept": "Energía", "monthly_amount": 8000.00,
        })
        cid = create.json()["id"]
        response = client.patch(f"/api/v1/production/costs/fixed/{cid}", json={
            "monthly_amount": 9000.00,
        })
        assert response.status_code == 200
        assert response.json()["monthly_amount"] == 9000.00

    def test_delete_fixed_cost(self, client):
        """Test soft-delete."""
        create = client.post("/api/v1/production/costs/fixed", json={
            "category": "OTHER", "concept": "Test Cost", "monthly_amount": 100.00,
        })
        cid = create.json()["id"]
        response = client.delete(f"/api/v1/production/costs/fixed/{cid}")
        assert response.status_code == 204

    def test_set_production_target(self, client):
        """Test setting production target with auto-calculation."""
        self._seed_costs(client)

        response = client.post("/api/v1/production/costs/target", json={
            "period": "2026-02",
            "target_liters_monthly": 1800.00,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["target_liters_monthly"] == 1800.00
        assert data["total_fixed_cost"] == 57900.00
        assert data["fixed_cost_per_liter"] == 32.17  # 57900 / 1800
        assert data["is_current"] is True

    def test_get_current_target(self, client):
        """Test retrieving current target."""
        self._seed_costs(client)
        client.post("/api/v1/production/costs/target", json={
            "period": "DEFAULT",
            "target_liters_monthly": 1800.00,
        })
        response = client.get("/api/v1/production/costs/target")
        assert response.status_code == 200
        assert response.json()["fixed_cost_per_liter"] == 32.17

    def test_cost_summary(self, client):
        """Test cost summary endpoint."""
        self._seed_costs(client)
        client.post("/api/v1/production/costs/target", json={
            "period": "DEFAULT",
            "target_liters_monthly": 1800.00,
        })

        response = client.get("/api/v1/production/costs/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_fixed_monthly"] == 57900.00
        assert data["target_liters"] == 1800.00
        assert data["fixed_cost_per_liter"] == 32.17
        assert len(data["cost_breakdown"]) >= 7

    def test_new_target_replaces_current(self, client):
        """Test that setting new target deactivates previous."""
        self._seed_costs(client)
        client.post("/api/v1/production/costs/target", json={
            "period": "2026-01",
            "target_liters_monthly": 1500.00,
        })
        client.post("/api/v1/production/costs/target", json={
            "period": "2026-02",
            "target_liters_monthly": 1800.00,
        })
        response = client.get("/api/v1/production/costs/target")
        assert response.json()["period"] == "2026-02"
