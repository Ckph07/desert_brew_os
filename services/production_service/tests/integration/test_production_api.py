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
