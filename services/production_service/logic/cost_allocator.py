"""
Cost Allocator - FIFO allocation from StockBatch inventory.

Links Production Service to Inventory Service for precise cost tracking.
"""
from sqlalchemy.orm import Session
from models.production_batch import ProductionBatch
from models.recipe import Recipe
from models.batch_ingredient_allocation import BatchIngredientAllocation
from typing import Dict, List
from decimal import Decimal


class InsufficientStockError(Exception):
    """Raised when there isn't enough stock to allocate."""
    pass


class CostAllocator:
    """
    Allocate ingredient costs from StockBatch using FIFO.
    
    Note: This is a placeholder for Sprint 4. Full integration with
    Inventory Service StockBatch (from Sprint 1) requires API calls
    or direct database access.
    
    For Sprint 4, we'll use mock data. Sprint 4.5 will integrate real FIFO.
    """
    
    @staticmethod
    def allocate_batch_costs(
        batch: ProductionBatch,
        recipe: Recipe,
        db: Session,
        labor_cost: float = 50.00,  # Fixed for Sprint 4
        overhead_cost: float = 30.00  # Fixed for Sprint 4
    ) -> Dict[str, float]:
        """
        Allocate costs from inventory using FIFO.
        
        Args:
            batch: ProductionBatch to allocate costs for
            recipe: Recipe with ingredient requirements
            db: Database session
            labor_cost: Fixed labor cost per batch
            overhead_cost: Fixed overhead cost per batch
            
        Returns:
            Dictionary with cost breakdown
            
        Raises:
            InsufficientStockError: If not enough inventory
        """
        allocations = []
        
        # Cost breakdown
        malt_cost = 0.0
        hops_cost = 0.0
        yeast_cost = 0.0
        water_cost = 0.0
        
        # Allocate fermentables (malts)
        if recipe.fermentables:
            for ferm in recipe.fermentables:
                cost = CostAllocator._allocate_fermentable(
                    batch=batch,
                    ingredient_name=ferm['name'],
                    required_kg=ferm['amount_kg'],
                    db=db
                )
                malt_cost += cost['total_cost']
                allocations.extend(cost['allocations'])
        
        # Allocate hops
        if recipe.hops:
            for hop in recipe.hops:
                cost = CostAllocator._allocate_hop(
                    batch=batch,
                    ingredient_name=hop['name'],
                    required_g=hop['amount_g'],
                    db=db
                )
                hops_cost += cost['total_cost']
                allocations.extend(cost['allocations'])
        
        # Allocate yeast (simplified - single cost)
        if recipe.yeast:
            yeast_cost = 15.00 * len(recipe.yeast)  # Fixed $15/packet
        
        # Water cost (placeholder - Sprint 5 will use WaterProductionRun)
        water_liters = float(recipe.batch_size_liters) * 1.5  # Assume 1.5x batch size for process water
        water_cost = water_liters * 0.50  # $0.50/liter placeholder
        
        # Calculate totals
        total_cost = malt_cost + hops_cost + yeast_cost + water_cost + labor_cost + overhead_cost
        
        # Update batch
        batch.malt_cost = Decimal(str(malt_cost))
        batch.hops_cost = Decimal(str(hops_cost))
        batch.yeast_cost = Decimal(str(yeast_cost))
        batch.water_cost = Decimal(str(water_cost))
        batch.labor_cost = Decimal(str(labor_cost))
        batch.overhead_cost = Decimal(str(overhead_cost))
        batch.total_cost = Decimal(str(total_cost))
        
        # Calculate cost per liter (will be updated when actual_volume_liters is set)
        if batch.actual_volume_liters:
            batch.cost_per_liter = batch.total_cost / batch.actual_volume_liters
        elif batch.planned_volume_liters:
            batch.cost_per_liter = batch.total_cost / batch.planned_volume_liters
        
        # Save allocations
        db.add_all(allocations)
        
        return {
            'malt_cost': malt_cost,
            'hops_cost': hops_cost,
            'yeast_cost': yeast_cost,
            'water_cost': water_cost,
            'labor_cost': labor_cost,
            'overhead_cost': overhead_cost,
            'total_cost': total_cost,
            'cost_per_liter': float(batch.cost_per_liter) if batch.cost_per_liter else 0.0
        }
    
    @staticmethod
    def _allocate_fermentable(
        batch: ProductionBatch,
        ingredient_name: str,
        required_kg: float,
        db: Session
    ) -> Dict:
        """
        Allocate fermentable from StockBatch using FIFO.
        
        PLACEHOLDER FOR SPRINT 4:
        Uses mock data. Real implementation in Sprint 4.5 will query
        Inventory Service StockBatch table.
        """
        # Mock FIFO allocation
        # TODO Sprint 4.5: Query actual StockBatch from inventory_service
        
        # Mock data: assume we have stock at $15/kg
        unit_cost = 15.00
        total_cost = required_kg * unit_cost
        
        # Create allocation record
        allocation = BatchIngredientAllocation(
            production_batch_id=batch.id,
            stock_batch_id=999,  # Mock ID
            ingredient_name=ingredient_name,
            ingredient_category='MALT',
            quantity_consumed=Decimal(str(required_kg)),
            unit_measure='KG',
            unit_cost=Decimal(str(unit_cost)),
            total_cost=Decimal(str(total_cost)),
            stock_batch_number='MOCK-BATCH-001',
            supplier_name='Mock Supplier'
        )
        
        return {
            'total_cost': total_cost,
            'allocations': [allocation]
        }
    
    @staticmethod
    def _allocate_hop(
        batch: ProductionBatch,
        ingredient_name: str,
        required_g: float,
        db: Session
    ) -> Dict:
        """
        Allocate hops from StockBatch using FIFO.
        
        PLACEHOLDER FOR SPRINT 4.
        """
        # Mock data: assume hops at $30/kg = $0.03/g
        unit_cost_per_g = 0.03
        total_cost = required_g * unit_cost_per_g
        
        allocation = BatchIngredientAllocation(
            production_batch_id=batch.id,
            stock_batch_id=998,  # Mock ID
            ingredient_name=ingredient_name,
            ingredient_category='HOP',
            quantity_consumed=Decimal(str(required_g)),
            unit_measure='G',
            unit_cost=Decimal('0.03'),
            total_cost=Decimal(str(total_cost)),
            stock_batch_number='MOCK-HOP-001',
            supplier_name='Mock Hop Supplier'
        )
        
        return {
            'total_cost': total_cost,
            'allocations': [allocation]
        }
