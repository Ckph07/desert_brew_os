"""
HTTP client for Finance Service.
"""
import httpx
import os
from typing import Dict
from decimal import Decimal


class FinanceServiceClient:
    """HTTP client for Finance Service API."""
    
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("FINANCE_SERVICE_URL", "http://localhost:8005")
        self.timeout = 10.0
    
    async def create_internal_transfer(
        self,
        origin_type: str,
        quantity: float,
        unit_measure: str,
        unit_cost: float,
        product_sku: str,
        product_name: str,
        profit_center_from: str = "factory",
        profit_center_to: str = "taproom",
        notes: str | None = None,
        created_by_user_id: int | None = None,
    ) -> Dict:
        """
        Create InternalTransfer (Factory → Taproom) aligned with Finance API schema.
        """
        payload = {
            "origin_type": origin_type,
            "quantity": quantity,
            "unit_measure": unit_measure,
            "unit_cost": unit_cost,
            "product_sku": product_sku,
            "product_name": product_name,
            "from_profit_center": profit_center_from,
            "to_profit_center": profit_center_to,
            "notes": notes,
            "created_by_user_id": created_by_user_id,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/finance/internal-transfers",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    
    async def get_profit_center_summary(
        self,
        profit_center_id: str
    ) -> Dict:
        """Get P&L summary for profit center."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/finance/profit-center/{profit_center_id}/summary"
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """Check if Finance Service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Dependency injection
def get_finance_client() -> FinanceServiceClient:
    """FastAPI dependency for FinanceServiceClient."""
    return FinanceServiceClient()
