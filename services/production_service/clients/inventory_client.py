"""
HTTP client for Inventory Service.
"""
import httpx
from typing import List, Dict, Optional
from decimal import Decimal


class InventoryServiceClient:
    """HTTP client for Inventory Service API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.timeout = 10.0
    
    async def get_available_stock_batches(
        self,
        ingredient_name: str,
        min_quantity: float = 0.0
    ) -> List[Dict]:
        """
        Get available StockBatches for ingredient (FIFO order).
        
        Returns list ordered by created_at ASC (oldest first).
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/inventory/stock-batches",
                params={
                    "ingredient_name": ingredient_name,
                    "available_only": True,
                    "min_quantity": min_quantity,
                    "sort": "created_at_asc"  # FIFO
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def consume_stock(
        self,
        stock_batch_id: int,
        quantity: float,
        unit: str,
        production_batch_id: int,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Consume quantity from StockBatch.
        
        Raises:
            httpx.HTTPStatusError: If insufficient quantity or batch not found
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/inventory/stock-batches/{stock_batch_id}/consume",
                json={
                    "quantity": quantity,
                    "unit": unit,
                    "reason": reason or f"Production Batch #{production_batch_id}"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def create_finished_product(
        self,
        production_batch_id: int,
        sku: str,
        volume_liters: float,
        unit_cost: float,
        container_type: str = "KEG",
        location: str = "COLD_ROOM"
    ) -> Dict:
        """
        Create FinishedProductInventory.
        
        Args:
            production_batch_id: ID of completed production batch
            sku: Product SKU (e.g., recipe name or product code)
            volume_liters: Total volume produced
            unit_cost: Cost per liter
            container_type: KEG, BOTTLE, or CAGUAMA
            location: Storage location
        
        Returns:
            Created FinishedProductInventory as dict
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/inventory/finished-products",
                json={
                    "production_batch_id": production_batch_id,
                    "sku": sku,
                    "volume_liters": volume_liters,
                    "unit_cost": unit_cost,
                    "container_type": container_type,
                    "location": location,
                    "origin_type": "HOUSE"  # Always HOUSE for production
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """Check if Inventory Service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Dependency injection
def get_inventory_client() -> InventoryServiceClient:
    """FastAPI dependency for InventoryServiceClient."""
    return InventoryServiceClient()
