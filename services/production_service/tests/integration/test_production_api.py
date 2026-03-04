"""
Integration tests for Production API.
"""
import pytest
import os


class TestRecipeAPI:
    """Test recipe endpoints."""
    
    def test_import_beersmith_recipe(self, client):
        """Test importing .bsmx file."""
        # Get sample file
        test_dir = os.path.dirname(os.path.dirname(__file__))
        sample_path = os.path.join(test_dir, 'fixtures', 'sample_ipa.bsmx')
        
        with open(sample_path, 'rb') as f:
            response = client.post(
                "/api/v1/production/recipes/import",
                files={"file": ("sample_ipa.bsmx", f, "application/xml")}
            )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data['name'] == "American IPA"
        assert data['batch_size_liters'] == 20.0
        assert len(data['fermentables']) == 2
        assert len(data['hops']) == 3
        assert len(data['yeast']) == 1

    def test_create_recipe_manual(self, client):
        """Test creating a recipe manually via JSON."""
        response = client.post("/api/v1/production/recipes", json={
            "name": "Desértica Blonde Ale",
            "style": "Blonde Ale",
            "brewer": "Carlos",
            "batch_size_liters": 40.0,
            "fermentables": [
                {"name": "Malta Pale Ale / Pilsen", "amount_kg": 7.0, "color_srm": 2.0, "type": "Grain"},
                {"name": "Malta Munich", "amount_kg": 1.0, "color_srm": 9.0, "type": "Grain"},
            ],
            "hops": [
                {"name": "Saaz", "amount_g": 30.0, "time_min": 60, "use": "Boil", "alpha_acid": 3.5},
            ],
            "yeast": [
                {"name": "SafAle US-05", "lab": "Fermentis", "type": "Ale"},
            ],
            "mash_steps": [
                {"step": "Mash In", "temp_c": 67.0, "time_min": 60},
            ],
            "expected_og": 1.048,
            "expected_fg": 1.010,
            "expected_abv": 4.98,
            "ibu": 20.0,
            "brewhouse_efficiency": 75.0,
            "notes": "Receta para 40L, fermentar a 18°C",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Desértica Blonde Ale"
        assert data["brewer"] == "Carlos"
        assert data["batch_size_liters"] == 40.0
        assert len(data["fermentables"]) == 2
        assert len(data["hops"]) == 1
        assert data["mash_steps"][0]["temp_c"] == 67.0

    def test_create_recipe_minimal(self, client):
        """Test creating a recipe with only required fields."""
        response = client.post("/api/v1/production/recipes", json={
            "name": "Test Recipe",
            "batch_size_liters": 20.0,
            "fermentables": [
                {"name": "Pale Malt", "amount_kg": 5.0},
            ],
            "yeast": [
                {"name": "US-05"},
            ],
        })
        assert response.status_code == 201
        assert response.json()["hops"] == []

    def test_update_recipe(self, client, sample_recipe):
        """Test updating an existing recipe."""
        response = client.patch(
            f"/api/v1/production/recipes/{sample_recipe.id}",
            json={"style": "West Coast IPA", "ibu": 75.0}
        )
        assert response.status_code == 200
        assert response.json()["style"] == "West Coast IPA"
        assert response.json()["ibu"] == 75.0

    def test_create_recipe_validation_error(self, client):
        """Test validation error — missing fermentables."""
        response = client.post("/api/v1/production/recipes", json={
            "name": "Bad Recipe",
            "batch_size_liters": 20.0,
            "fermentables": [],
            "yeast": [{"name": "US-05"}],
        })
        assert response.status_code == 422
    
    def test_list_recipes(self, client, sample_recipe):
        """Test listing recipes."""
        response = client.get("/api/v1/production/recipes")
        
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) >= 1
    
    def test_get_recipe(self, client, sample_recipe):
        """Test getting recipe details."""
        response = client.get(f"/api/v1/production/recipes/{sample_recipe.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == sample_recipe.id
        assert data['name'] == sample_recipe.name

    def test_delete_recipe(self, client):
        """Test deleting an unused recipe."""
        create_response = client.post("/api/v1/production/recipes", json={
            "name": "Recipe To Delete",
            "batch_size_liters": 20.0,
            "fermentables": [{"name": "Pale Malt", "amount_kg": 5.0}],
            "yeast": [{"name": "US-05"}],
        })
        assert create_response.status_code == 201
        recipe_id = create_response.json()["id"]

        delete_response = client.delete(f"/api/v1/production/recipes/{recipe_id}")
        assert delete_response.status_code == 204

        get_response = client.get(f"/api/v1/production/recipes/{recipe_id}")
        assert get_response.status_code == 404


class TestProductionBatchAPI:
    """Test production batch endpoints."""
    
    def test_create_batch(self, client, sample_recipe):
        """Test creating production batch."""
        response = client.post("/api/v1/production/batches", json={
            "recipe_id": sample_recipe.id,
            "batch_number": "IPA-2026-001",
            "planned_volume_liters": 20.0,
            "notes": "First batch of the year"
        })
        
        assert response.status_code == 201
        data = response.json()
        
        assert data['batch_number'] == "IPA-2026-001"
        assert data['status'] == "planned"
        assert data['recipe_id'] == sample_recipe.id
    
    def test_start_brewing(self, client, sample_recipe):
        """Test starting brewing (PLANNED → BREWING)."""
        # Create batch
        batch_resp = client.post("/api/v1/production/batches", json={
            "recipe_id": sample_recipe.id,
            "batch_number": "IPA-2026-002",
            "planned_volume_liters": 20.0
        })
        batch_id = batch_resp.json()['id']
        
        # Start brewing
        response = client.patch(f"/api/v1/production/batches/{batch_id}/start-brewing")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['previous_status'] == "planned"
        assert data['new_status'] == "brewing"
        assert "Total cost allocated" in data['message']
    
    def test_full_batch_lifecycle(self, client, sample_recipe):
        """Test complete batch lifecycle."""
        # 1. Create batch
        create_resp = client.post("/api/v1/production/batches", json={
            "recipe_id": sample_recipe.id,
            "batch_number": "IPA-2026-003",
            "planned_volume_liters": 20.0
        })
        batch_id = create_resp.json()['id']
        
        # 2. Start brewing
        brew_resp = client.patch(f"/api/v1/production/batches/{batch_id}/start-brewing")
        assert brew_resp.status_code == 200
        
        # 3. Start fermenting
        ferm_resp = client.patch(f"/api/v1/production/batches/{batch_id}/start-fermenting")
        assert ferm_resp.status_code == 200
        assert ferm_resp.json()['new_status'] == "fermenting"
        
        # 4. Get batch details
        detail_resp = client.get(f"/api/v1/production/batches/{batch_id}")
        assert detail_resp.status_code == 200
        batch = detail_resp.json()
        
        assert batch['status'] == "fermenting"
        assert batch['total_cost'] is not None
        assert batch['malt_cost'] is not None

    def test_transition_to_conditioning_and_packaging(self, client, sample_recipe):
        """Test FERMENTING → CONDITIONING → PACKAGING transitions."""
        create_resp = client.post("/api/v1/production/batches", json={
            "recipe_id": sample_recipe.id,
            "batch_number": "IPA-2026-003B",
            "planned_volume_liters": 20.0
        })
        batch_id = create_resp.json()['id']

        brew_resp = client.patch(f"/api/v1/production/batches/{batch_id}/start-brewing")
        assert brew_resp.status_code == 200

        ferm_resp = client.patch(f"/api/v1/production/batches/{batch_id}/start-fermenting")
        assert ferm_resp.status_code == 200

        conditioning_resp = client.patch(
            f"/api/v1/production/batches/{batch_id}/start-conditioning"
        )
        assert conditioning_resp.status_code == 200
        assert conditioning_resp.json()["new_status"] == "conditioning"

        packaging_resp = client.patch(
            f"/api/v1/production/batches/{batch_id}/start-packaging"
        )
        assert packaging_resp.status_code == 200
        assert packaging_resp.json()["new_status"] == "packaging"

    def test_batch_uses_recipe_snapshot_for_costing(self, client, sample_recipe, db_session):
        """Batch costing should use recipe snapshot captured at planning time."""
        from models.batch_ingredient_allocation import BatchIngredientAllocation

        create_resp = client.post("/api/v1/production/batches", json={
            "recipe_id": sample_recipe.id,
            "batch_number": "IPA-2026-003C",
            "planned_volume_liters": 20.0
        })
        assert create_resp.status_code == 201
        batch_id = create_resp.json()["id"]

        # Update the source recipe after batch planning.
        patch_resp = client.patch(
            f"/api/v1/production/recipes/{sample_recipe.id}",
            json={
                "fermentables": [
                    {"name": "Maris Otter", "amount_kg": 9.0, "type": "Grain"}
                ]
            },
        )
        assert patch_resp.status_code == 200

        brew_resp = client.patch(f"/api/v1/production/batches/{batch_id}/start-brewing")
        assert brew_resp.status_code == 200

        malt_allocations = db_session.query(BatchIngredientAllocation).filter(
            BatchIngredientAllocation.production_batch_id == batch_id,
            BatchIngredientAllocation.ingredient_category == "MALT",
        ).all()

        total_malt_kg = sum(float(a.quantity_consumed) for a in malt_allocations)
        assert total_malt_kg == pytest.approx(5.0, rel=1e-6)

    def test_cancel_batch(self, client, sample_recipe):
        """Test cancelling a batch with reason."""
        create_resp = client.post("/api/v1/production/batches", json={
            "recipe_id": sample_recipe.id,
            "batch_number": "IPA-2026-003D",
            "planned_volume_liters": 20.0
        })
        batch_id = create_resp.json()["id"]

        cancel_resp = client.patch(
            f"/api/v1/production/batches/{batch_id}/cancel",
            json={"reason": "Contaminacion detectada"},
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["new_status"] == "cancelled"
        assert "Contaminacion detectada" in cancel_resp.json()["message"]

    def test_validate_recipe_stock(self, client, sample_recipe):
        """Validate stock availability for recipe ingredients."""
        response = client.post(
            f"/api/v1/production/recipes/{sample_recipe.id}/validate-stock",
            json={"planned_volume_liters": 20.0},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["recipe_id"] == sample_recipe.id
        assert payload["all_available"] is True
        assert len(payload["items"]) >= 3  # malt + hop + yeast
        assert all(item["status"] == "OK" for item in payload["items"])

    def test_validate_recipe_stock_insufficient(self, client, sample_recipe):
        """Validation should flag insufficient inventory for scaled batches."""
        response = client.post(
            f"/api/v1/production/recipes/{sample_recipe.id}/validate-stock",
            json={"planned_volume_liters": 5000.0},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["all_available"] is False
        assert any(item["status"] == "INSUFFICIENT" for item in payload["items"])

    def test_validate_recipe_stock_uses_yeast_amount_packets(self, client):
        """Validation should respect yeast amount_packets and volume scaling."""
        recipe_resp = client.post("/api/v1/production/recipes", json={
            "name": "Double Yeast IPA",
            "batch_size_liters": 20.0,
            "fermentables": [{"name": "Pale Malt", "amount_kg": 5.0}],
            "hops": [{"name": "Cascade", "amount_g": 40.0}],
            "yeast": [{"name": "US-05", "amount_packets": 2.0}],
        })
        assert recipe_resp.status_code == 201
        recipe_id = recipe_resp.json()["id"]

        response = client.post(
            f"/api/v1/production/recipes/{recipe_id}/validate-stock",
            json={"planned_volume_liters": 40.0},
        )
        assert response.status_code == 200
        payload = response.json()
        yeast_item = next(item for item in payload["items"] if item["ingredient_type"] == "YEAST")
        assert yeast_item["required_quantity"] == pytest.approx(4.0, rel=1e-6)

    def test_start_brewing_preflight_avoids_partial_consumption(self, client, sample_recipe):
        """If one ingredient is missing, no stock should be consumed before failing."""
        from main import app
        from clients.inventory_client import get_inventory_client

        consume_calls = []

        class InsufficientHopInventoryClient:
            async def get_available_stock_batches(self, ingredient_name, min_quantity=0.01):
                if ingredient_name == "Cascade":
                    return []
                return [
                    {
                        "id": 1,
                        "batch_number": f"MOCK-{ingredient_name[:4].upper()}-001",
                        "sku": ingredient_name,
                        "available_quantity": 100.0,
                        "unit_cost": 25.00,
                        "unit_measure": "KG",
                        "supplier_name": "Test Supplier",
                    }
                ]

            async def consume_stock(self, stock_batch_id, quantity, unit, production_batch_id, reason=None):
                consume_calls.append((stock_batch_id, quantity, unit))
                return {"status": "consumed"}

            async def create_finished_product(self, *args, **kwargs):
                return {}

            async def health_check(self):
                return True

        app.dependency_overrides[get_inventory_client] = lambda: InsufficientHopInventoryClient()
        try:
            create_resp = client.post("/api/v1/production/batches", json={
                "recipe_id": sample_recipe.id,
                "batch_number": "IPA-2026-003E",
                "planned_volume_liters": 20.0
            })
            assert create_resp.status_code == 201
            batch_id = create_resp.json()["id"]

            brew_resp = client.patch(f"/api/v1/production/batches/{batch_id}/start-brewing")
            assert brew_resp.status_code == 400
            assert "Insufficient stock" in brew_resp.text
            assert consume_calls == []
        finally:
            app.dependency_overrides.pop(get_inventory_client, None)
    
    def test_complete_batch(self, client, sample_recipe, db_session):
        """Test completing batch with actual volume."""
        from models.production_batch import ProductionBatch, BatchStatus
        
        # Create batch in PACKAGING status
        batch = ProductionBatch(
            batch_number="IPA-2026-004",
            recipe_id=sample_recipe.id,
            recipe_name=sample_recipe.name,
            planned_volume_liters=20.0,
            status=BatchStatus.PACKAGING.value,
            total_cost=500.00
        )
        db_session.add(batch)
        db_session.commit()
        
        # Complete batch
        response = client.patch(
            f"/api/v1/production/batches/{batch.id}/complete",
            json={
                "actual_volume_liters": 19.5,
                "actual_og": 1.064,
                "actual_fg": 1.011
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['new_status'] == "completed"
        assert "19.50L" in data['message'] or "Volume" in data['message']
    
    def test_get_cost_breakdown(self, client, sample_recipe, db_session):
        """Test cost breakdown endpoint."""
        from models.production_batch import ProductionBatch, BatchStatus
        
        # Create batch with costs
        batch = ProductionBatch(
            batch_number="IPA-2026-005",
            recipe_id=sample_recipe.id,
            recipe_name=sample_recipe.name,
            planned_volume_liters=20.0,
            status=BatchStatus.BREWING.value,
            total_cost=500.00,
            malt_cost=200.00,
            hops_cost=75.00,
            yeast_cost=15.00,
            water_cost=50.00,
            labor_cost=50.00,
            overhead_cost=30.00,
            cost_per_liter=25.00
        )
        db_session.add(batch)
        db_session.commit()
        
        response = client.get(f"/api/v1/production/batches/{batch.id}/cost-breakdown")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['batch_number'] == "IPA-2026-005"
        assert data['total_cost'] == 500.00
        assert data['breakdown']['malt'] == 200.00
        assert data['breakdown']['hops'] == 75.00
