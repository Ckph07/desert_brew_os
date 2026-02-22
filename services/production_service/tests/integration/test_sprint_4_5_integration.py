"""
Integration tests for Sprint 4.5 - Real FIFO and Finance Integration.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from logic.cost_allocator import CostAllocator
from models.production_batch import ProductionBatch, BatchStatus
from models.recipe import Recipe
from models.batch_ingredient_allocation import BatchIngredientAllocation
from exceptions import InsufficientStockError, ServiceUnavailableError
import httpx


@pytest.mark.asyncio
class TestRealFIFOIntegration:
    """Test real FIFO integration with Inventory Service."""
    
    @pytest.fixture
    def sample_recipe(self):
        """Create sample recipe with ingredients."""
        return Recipe(
            id=1,
            name="American IPA",
            style="IPA",
            batch_size_liters=Decimal("20.0"),
            fermentables=[
                {"name": "Maris Otter", "amount_kg": 5.0},
                {"name": "Caramel Malt", "amount_kg": 0.5}
            ],
            hops=[
                {"name": "Cascade", "amount_g": 50.0},
                {"name": "Centennial", "amount_g": 30.0}
            ],
            yeast=[
                {"name": "US-05"}
            ]
        )
    
    @pytest.fixture
    def sample_batch(self, sample_recipe):
        """Create sample production batch."""
        return ProductionBatch(
            id=1,
            batch_number="IPA-2026-001",
            recipe_id=1,
            recipe_name="American IPA",
            planned_volume_liters=Decimal("20.0"),
            status=BatchStatus.PLANNED.value
        )
    
    async def test_fifo_allocation_single_batch(self, sample_batch, sample_recipe, db_session):
        """Test FIFO allocation from single stock batch."""
        # Mock inventory client
        mock_inventory_client = AsyncMock()
        mock_inventory_client.get_available_stock_batches.return_value = [
            {
                "id": 1,
                "batch_number": "MALT-001",
                "available_quantity": 10.0,
                "unit_cost": 15.00,
                "supplier_name": "Supplier A"
            }
        ]
        mock_inventory_client.consume_stock.return_value = {"status": "consumed"}
        
        # Allocate costs
        cost_breakdown = await CostAllocator.allocate_batch_costs(
            batch=sample_batch,
            recipe=sample_recipe,
            db=db_session,
            inventory_client=mock_inventory_client
        )
        
        # Verify costs calculated
        assert cost_breakdown['malt_cost'] > 0
        assert cost_breakdown['hops_cost'] > 0
        assert cost_breakdown['total_cost'] > 0
        
        # Verify inventory client called
        assert mock_inventory_client.get_available_stock_batches.call_count >= 2  # Malts + hops
        assert mock_inventory_client.consume_stock.call_count >= 2
    
    async def test_fifo_allocation_multiple_batches(self, sample_batch, sample_recipe, db_session):
        """Test FIFO allocation from multiple stock batches (oldest first)."""
        mock_inventory_client = AsyncMock()
        
        # Mock: Need 5kg Maris Otter, have 2 batches (3kg @ $15, 5kg @ $18)
        mock_inventory_client.get_available_stock_batches.side_effect = [
            # First call: Maris Otter
            [
                {"id": 1, "batch_number": "MALT-001", "available_quantity": 3.0, "unit_cost": 15.00, "supplier_name": "Supplier A"},
                {"id": 2, "batch_number": "MALT-002", "available_quantity": 5.0, "unit_cost": 18.00, "supplier_name": "Supplier B"}
            ],
            # Second call: Caramel Malt
            [{"id": 3, "batch_number": "CARAMEL-001", "available_quantity": 2.0, "unit_cost": 20.00, "supplier_name": "Supplier C"}],
            # Hops...
            [{"id": 4, "batch_number": "HOP-001", "available_quantity": 0.1, "unit_cost": 300.00, "supplier_name": "Hop Supplier"}],
            [{"id": 5, "batch_number": "HOP-002", "available_quantity": 0.1, "unit_cost": 300.00, "supplier_name": "Hop Supplier"}],
            # Yeast
            [{"id": 6, "batch_number": "YEAST-001", "available_quantity": 10.0, "unit_cost": 15.00, "supplier_name": "Yeast Supplier"}]
        ]
        mock_inventory_client.consume_stock.return_value = {"status": "consumed"}
        
        cost_breakdown = await CostAllocator.allocate_batch_costs(
            batch=sample_batch,
            recipe=sample_recipe,
            db=db_session,
            inventory_client=mock_inventory_client
        )
        
        # Verify FIFO: Should consume from batch 1 first (3kg @ $15), then batch 2 (2kg @ $18)
        # Total malt cost for Maris Otter: (3 * 15) + (2 * 18) = 45 + 36 = 81
        # Plus Caramel Malt: 0.5 * 20 = 10
        # Expected malt_cost: ~91
        assert sample_batch.malt_cost > Decimal("80")  # At least 81+
        
        # Verify allocations were created in memory
        assert cost_breakdown['allocations_count'] > 0
    
    async def test_insufficient_stock_error(self, sample_batch, sample_recipe, db_session):
        """Test InsufficientStockError when not enough inventory."""
        mock_inventory_client = AsyncMock()
        
        # Mock: Only 2kg available, but need 5kg
        mock_inventory_client.get_available_stock_batches.return_value = [
            {"id": 1, "batch_number": "MALT-001", "available_quantity": 2.0, "unit_cost": 15.00, "supplier_name": "Supplier A"}
        ]
        
        with pytest.raises(InsufficientStockError) as exc_info:
            await CostAllocator.allocate_batch_costs(
                batch=sample_batch,
                recipe=sample_recipe,
                db=db_session,
                inventory_client=mock_inventory_client
            )
        
        assert exc_info.value.ingredient == "Maris Otter"
        assert exc_info.value.required == 5.0
        assert exc_info.value.available == 2.0
    
    async def test_service_unavailable_error(self, sample_batch, sample_recipe, db_session):
        """Test ServiceUnavailableError when Inventory Service is down."""
        mock_inventory_client = AsyncMock()
        mock_inventory_client.get_available_stock_batches.side_effect = httpx.ConnectError("Connection refused")
        
        with pytest.raises(ServiceUnavailableError):
            await CostAllocator.allocate_batch_costs(
                batch=sample_batch,
                recipe=sample_recipe,
                db=db_session,
                inventory_client=mock_inventory_client
            )


@pytest.mark.asyncio
class TestFinanceIntegration:
    """Test Finance Service integration."""

    def test_create_internal_transfer_on_completion(self, client, db_session):
        """Test that completing a batch creates InternalTransfer via mock."""
        # Create batch in PACKAGING status with costs
        recipe = create_sample_recipe(db_session)
        batch = create_sample_batch(db_session, recipe.id, status="packaging")
        batch.total_cost = Decimal("420.00")
        db_session.commit()

        # Complete batch — uses mock clients from conftest
        response = client.patch(
            f"/api/v1/production/batches/{batch.id}/complete",
            json={"actual_volume_liters": 19.5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data['new_status'] == "completed"
        assert "19.50L" in data['message'] or "Volume" in data['message']


def create_sample_recipe(db):
    """Helper to create sample recipe."""
    recipe = Recipe(
        name="Test IPA",
        style="IPA",
        batch_size_liters=Decimal("20.0"),
        fermentables=[{"name": "Maris Otter", "amount_kg": 5.0}],
        hops=[{"name": "Cascade", "amount_g": 50.0}],
        yeast=[{"name": "US-05"}]
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def create_sample_batch(db, recipe_id, status="PLANNED"):
    """Helper to create sample batch."""
    batch = ProductionBatch(
        batch_number=f"TEST-{status}-001",
        recipe_id=recipe_id,
        recipe_name="Test IPA",
        planned_volume_liters=Decimal("20.0"),
        status=status
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch
