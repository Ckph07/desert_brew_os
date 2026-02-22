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
