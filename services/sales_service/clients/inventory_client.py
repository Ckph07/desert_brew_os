"""
HTTP client for Inventory Service — stock deduction on sales.

Purpose: When a sales note is confirmed, deduct the corresponding finished
product inventory. Follows the same async httpx pattern as Production Service.

Integration Flow:
1. Sales note CONFIRMED → for each item with product_id
2. Look up product in Inventory Service finished products
3. Deduct quantity from available stock
4. Log the movement with reference to the note number
"""
import httpx
import os
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8001")


class InventoryServiceClient:
    """HTTP client for Inventory Service API."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or INVENTORY_SERVICE_URL
        self.timeout = 10.0

    async def deduct_finished_product(
        self,
        product_id: int,
        quantity: float,
        note_number: str,
        reason: Optional[str] = None,
    ) -> Dict:
        """
        Deduct quantity from a FinishedProductInventory record.

        Args:
            product_id: Inventory Service finished_product.id
            quantity: Amount to deduct
            note_number: Sales note number for audit trail
            reason: Optional reason string

        Returns:
            Updated product record from Inventory Service

        Raises:
            httpx.HTTPStatusError: If insufficient stock or product not found
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/inventory/finished-products/{product_id}",
                json={
                    "quantity_delta": -quantity,
                    "movement_reason": reason or f"Sales Note #{note_number}",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_finished_product_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Look up finished product by SKU.

        Returns:
            Product dict or None if not found
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/inventory/finished-products",
                params={"sku": sku, "available_only": True},
            )
            response.raise_for_status()
            products = response.json()
            return products[0] if products else None

    async def deduct_items_for_note(
        self,
        items: list,
        note_number: str,
    ) -> List[Dict]:
        """
        Deduct inventory for all items in a sales note.

        Only processes items that have a product_id (linked to catalog).
        Items without product_id (e.g., "Envío") are skipped.

        Args:
            items: List of SalesNoteItem
            note_number: Note number for audit trail

        Returns:
            List of deduction results
        """
        results = []
        for item in items:
            if not item.product_id:
                continue  # Skip items without product link (shipping, etc.)

            try:
                result = await self.deduct_finished_product(
                    product_id=item.product_id,
                    quantity=float(item.quantity),
                    note_number=note_number,
                    reason=f"Venta: {item.product_name} × {item.quantity}",
                )
                results.append({
                    "item_id": item.id,
                    "product_id": item.product_id,
                    "quantity_deducted": float(item.quantity),
                    "status": "OK",
                })
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"Failed to deduct inventory for item {item.id} "
                    f"(product_id={item.product_id}): {e.response.status_code}"
                )
                results.append({
                    "item_id": item.id,
                    "product_id": item.product_id,
                    "quantity_deducted": 0,
                    "status": f"ERROR: {e.response.status_code}",
                })
            except httpx.ConnectError:
                logger.warning("Inventory Service unreachable")
                results.append({
                    "item_id": item.id,
                    "product_id": item.product_id,
                    "quantity_deducted": 0,
                    "status": "ERROR: Inventory Service unreachable",
                })

        return results

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
