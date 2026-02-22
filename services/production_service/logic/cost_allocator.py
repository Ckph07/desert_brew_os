"""
Cost Allocator - Real FIFO allocation from Inventory Service StockBatch.

Sprint 4.5: Integrated with Inventory Service for precise cost tracking.
Sprint 5.5: Real fixed cost overhead from FixedMonthlyCost + ProductionTarget.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.production_batch import ProductionBatch
from models.recipe import Recipe
from models.batch_ingredient_allocation import BatchIngredientAllocation
from models.fixed_monthly_cost import FixedMonthlyCost, ProductionTarget
from clients.inventory_client import InventoryServiceClient
from exceptions import InsufficientStockError, ServiceUnavailableError
from typing import Dict, List
from decimal import Decimal
import httpx
import logging

logger = logging.getLogger(__name__)


class CostAllocator:
    """
    Allocate ingredient costs from StockBatch using real FIFO.
    
    Queries Inventory Service for available stock and consumes from oldest batches first.
    """
    
    @staticmethod
    def _get_fixed_cost_per_liter(db: Session) -> float:
        """
        Calculate fixed cost per liter from FixedMonthlyCost + ProductionTarget.

        Falls back to $32.17/L (default $57,900/1,800L) if no data.
        """
        # Try current target first
        target = db.query(ProductionTarget).filter(
            ProductionTarget.is_current == True
        ).first()

        if target and target.fixed_cost_per_liter:
            return float(target.fixed_cost_per_liter)

        # Calculate from active costs
        total_fixed = db.query(
            func.coalesce(func.sum(FixedMonthlyCost.monthly_amount), 0)
        ).filter(FixedMonthlyCost.is_active == True).scalar()

        total_fixed = float(total_fixed)
        if total_fixed == 0:
            logger.warning("No fixed costs configured. Using default $32.17/L")
            return 32.17  # Default fallback

        target_liters = float(target.target_liters_monthly) if target else 1800.0
        return round(total_fixed / target_liters, 2)

    @staticmethod
    async def allocate_batch_costs(
        batch: ProductionBatch,
        recipe: Recipe,
        db: Session,
        inventory_client: InventoryServiceClient,
        labor_cost: float = None,
        overhead_cost: float = None,
    ) -> Dict[str, float]:
        """
        Allocate costs from inventory using real FIFO from StockBatch.
        
        Args:
            batch: ProductionBatch to allocate costs for
            recipe: Recipe with ingredient requirements
            db: Database session
            inventory_client: Client for Inventory Service API
            labor_cost: Fixed labor cost per batch
            overhead_cost: Fixed overhead cost per batch
            
        Returns:
            Dictionary with cost breakdown
            
        Raises:
            InsufficientStockError: If not enough inventory
            ServiceUnavailableError: If Inventory Service is down
        """
        allocations = []
        
        # Cost breakdown
        malt_cost = 0.0
        hops_cost = 0.0
        yeast_cost = 0.0
        water_cost = 0.0
        
        try:
            # Allocate fermentables (malts) - Real FIFO
            if recipe.fermentables:
                for ferm in recipe.fermentables:
                    result = await CostAllocator._allocate_fermentable(
                        batch=batch,
                        ingredient_name=ferm['name'],
                        required_kg=ferm['amount_kg'],
                        inventory_client=inventory_client
                    )
                    malt_cost += result['total_cost']
                    allocations.extend(result['allocations'])
            
            # Allocate hops - Real FIFO
            if recipe.hops:
                for hop in recipe.hops:
                    result = await CostAllocator._allocate_hop(
                        batch=batch,
                        ingredient_name=hop['name'],
                        required_g=hop['amount_g'],
                        inventory_client=inventory_client
                    )
                    hops_cost += result['total_cost']
                    allocations.extend(result['allocations'])
            
            # Allocate yeast - Real FIFO
            if recipe.yeast:
                for yeast_item in recipe.yeast:
                    result = await CostAllocator._allocate_yeast(
                        batch=batch,
                        yeast_name=yeast_item['name'],
                        inventory_client=inventory_client
                    )
                    yeast_cost += result['total_cost']
                    allocations.extend(result['allocations'])
        
        except httpx.HTTPError as e:
            raise ServiceUnavailableError("Inventory Service", f"FIFO allocation: {str(e)}")
        
        # Water cost (placeholder - Sprint 5 will use WaterProductionRun)
        water_liters = float(recipe.batch_size_liters) * 1.5  # Assume 1.5x batch size
        water_cost = water_liters * 0.50  # $0.50/liter placeholder
        
        # Real fixed cost overhead from FixedMonthlyCost + ProductionTarget
        fixed_cost_per_liter = CostAllocator._get_fixed_cost_per_liter(db)
        batch_volume = float(batch.planned_volume_liters or 0)
        
        # If not provided, calculate from real fixed costs
        if overhead_cost is None:
            overhead_cost = round(fixed_cost_per_liter * batch_volume, 2)
        if labor_cost is None:
            labor_cost = 0.0  # Labor is now part of fixed costs (HR category)
        
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
        
        # Calculate cost per liter (based on planned volume initially)
        if batch.actual_volume_liters:
            batch.cost_per_liter = batch.total_cost / batch.actual_volume_liters
        elif batch.planned_volume_liters:
            batch.cost_per_liter = batch.total_cost / batch.planned_volume_liters
        
        # Save allocations to database
        db.add_all(allocations)
        
        return {
            'malt_cost': malt_cost,
            'hops_cost': hops_cost,
            'yeast_cost': yeast_cost,
            'water_cost': water_cost,
            'labor_cost': labor_cost,
            'overhead_cost': overhead_cost,
            'total_cost': total_cost,
            'cost_per_liter': float(batch.cost_per_liter) if batch.cost_per_liter else 0.0,
            'allocations_count': len(allocations)
        }
    
    @staticmethod
    async def _allocate_fermentable(
        batch: ProductionBatch,
        ingredient_name: str,
        required_kg: float,
        inventory_client: InventoryServiceClient
    ) -> Dict:
        """
        Allocate fermentable from StockBatch using real FIFO.
        
        Queries Inventory Service, consumes from oldest batches first.
        """
        # Get available stock batches (FIFO order: oldest first)
        stock_batches = await inventory_client.get_available_stock_batches(
            ingredient_name=ingredient_name,
            min_quantity=0.01
        )
        
        if not stock_batches:
            raise InsufficientStockError(ingredient_name, required_kg, 0.0, "KG")
        
        # Calculate total available
        total_available = sum(sb.get('available_quantity', 0.0) for sb in stock_batches)
        
        if total_available < required_kg:
            raise InsufficientStockError(ingredient_name, required_kg, total_available, "KG")
        
        # Allocate from oldest first (FIFO)
        allocations = []
        remaining = required_kg
        total_cost = 0.0
        
        for stock_batch in stock_batches:
            if remaining <= 0:
                break
            
            qty_to_consume = min(remaining, stock_batch['available_quantity'])
            unit_cost = float(stock_batch['unit_cost'])
            cost = qty_to_consume * unit_cost
            
            # Consume from Inventory Service
            await inventory_client.consume_stock(
                stock_batch_id=stock_batch['id'],
                quantity=qty_to_consume,
                unit="KG",
                production_batch_id=batch.id,
                reason=f"Production Batch #{batch.batch_number}"
            )
            
            # Create allocation record
            allocation = BatchIngredientAllocation(
                production_batch_id=batch.id,
                stock_batch_id=stock_batch['id'],
                ingredient_name=ingredient_name,
                ingredient_category='MALT',
                quantity_consumed=Decimal(str(qty_to_consume)),
                unit_measure='KG',
                unit_cost=Decimal(str(unit_cost)),
                total_cost=Decimal(str(cost)),
                stock_batch_number=stock_batch.get('batch_number', f"SB-{stock_batch['id']}"),
                supplier_name=stock_batch.get('supplier_name', 'Unknown')
            )
            allocations.append(allocation)
            
            remaining -= qty_to_consume
            total_cost += cost
        
        return {
            'total_cost': total_cost,
            'allocations': allocations
        }
    
    @staticmethod
    async def _allocate_hop(
        batch: ProductionBatch,
        ingredient_name: str,
        required_g: float,
        inventory_client: InventoryServiceClient
    ) -> Dict:
        """
        Allocate hops from StockBatch using real FIFO.
        
        Note: Hops are stored in KG in StockBatch, so we convert grams to kg.
        """
        required_kg = required_g / 1000.0  # Convert grams to kg
        
        # Get available stock batches
        stock_batches = await inventory_client.get_available_stock_batches(
            ingredient_name=ingredient_name,
            min_quantity=0.001  # 1 gram minimum
        )
        
        if not stock_batches:
            raise InsufficientStockError(ingredient_name, required_g, 0.0, "G")
        
        # Calculate total available (in grams)
        total_available_kg = sum(sb.get('available_quantity', 0.0) for sb in stock_batches)
        total_available_g = total_available_kg * 1000
        
        if total_available_g < required_g:
            raise InsufficientStockError(ingredient_name, required_g, total_available_g, "G")
        
        # Allocate from oldest first
        allocations = []
        remaining_kg = required_kg
        total_cost = 0.0
        
        for stock_batch in stock_batches:
            if remaining_kg <= 0:
                break
            
            qty_to_consume_kg = min(remaining_kg, stock_batch['available_quantity'])
            unit_cost_per_kg = float(stock_batch['unit_cost'])
            cost = qty_to_consume_kg * unit_cost_per_kg
            
            # Consume from Inventory Service (in KG)
            await inventory_client.consume_stock(
                stock_batch_id=stock_batch['id'],
                quantity=qty_to_consume_kg,
                unit="KG",
                production_batch_id=batch.id,
                reason=f"Production Batch #{batch.batch_number}"
            )
            
            # Create allocation record (store in grams for display)
            allocation = BatchIngredientAllocation(
                production_batch_id=batch.id,
                stock_batch_id=stock_batch['id'],
                ingredient_name=ingredient_name,
                ingredient_category='HOP',
                quantity_consumed=Decimal(str(qty_to_consume_kg * 1000)),  # Store as grams
                unit_measure='G',
                unit_cost=Decimal(str(unit_cost_per_kg / 1000)),  # Cost per gram
                total_cost=Decimal(str(cost)),
                stock_batch_number=stock_batch.get('batch_number', f"SB-{stock_batch['id']}"),
                supplier_name=stock_batch.get('supplier_name', 'Unknown')
            )
            allocations.append(allocation)
            
            remaining_kg -= qty_to_consume_kg
            total_cost += cost
        
        return {
            'total_cost': total_cost,
            'allocations': allocations
        }
    
    @staticmethod
    async def _allocate_yeast(
        batch: ProductionBatch,
        yeast_name: str,
        inventory_client: InventoryServiceClient
    ) -> Dict:
        """
        Allocate yeast from StockBatch using real FIFO.
        
        Yeast is typically 1 packet/sachet per batch.
        """
        required_packets = 1.0  # Simplified: 1 packet per yeast strain
        
        # Get available stock batches
        stock_batches = await inventory_client.get_available_stock_batches(
            ingredient_name=yeast_name,
            min_quantity=0.1
        )
        
        if not stock_batches or stock_batches[0]['available_quantity'] < required_packets:
            available = stock_batches[0]['available_quantity'] if stock_batches else 0.0
            raise InsufficientStockError(yeast_name, required_packets, available, "PACKET")
        
        # Use first (oldest) batch
        stock_batch = stock_batches[0]
        unit_cost = float(stock_batch['unit_cost'])
        cost = required_packets * unit_cost
        
        # Consume from Inventory Service
        await inventory_client.consume_stock(
            stock_batch_id=stock_batch['id'],
            quantity=required_packets,
            unit="PACKET",
            production_batch_id=batch.id,
            reason=f"Production Batch #{batch.batch_number}"
        )
        
        # Create allocation record
        allocation = BatchIngredientAllocation(
            production_batch_id=batch.id,
            stock_batch_id=stock_batch['id'],
            ingredient_name=yeast_name,
            ingredient_category='YEAST',
            quantity_consumed=Decimal(str(required_packets)),
            unit_measure='PACKET',
            unit_cost=Decimal(str(unit_cost)),
            total_cost=Decimal(str(cost)),
            stock_batch_number=stock_batch.get('batch_number', f"SB-{stock_batch['id']}"),
            supplier_name=stock_batch.get('supplier_name', 'Unknown')
        )
        
        return {
            'total_cost': cost,
            'allocations': [allocation]
        }
