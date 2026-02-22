"""
HTTP client for Finance Service.
"""
import httpx
from typing import Dict
from decimal import Decimal


class FinanceServiceClient:
    """HTTP client for Finance Service API."""
    
    def __init__(self, base_url: str = "http://localhost:8005"):
        self.base_url = base_url
        self.timeout = 10.0
    
    async def create_internal_transfer(
        self,
        origin_type: str,
        volume_liters: float,
        unit_cost: float,
        production_batch_id: int,
        profit_center_from: str = "factory",
        profit_center_to: str = "taproom"
    ) -> Dict:
        """
        Create InternalTransfer (Factory → Taproom).
        
        Args:
            origin_type: "HOUSE", "GUEST", "COMMERCIAL", or "MERCHANDISE"
            volume_liters: Volume transferred
            unit_cost: Factory cost per liter (before transfer pricing)
            production_batch_id: Source production batch
            profit_center_from: Source profit center (default: "factory")
            profit_center_to: Destination profit center (default: "taproom")
        
        Returns:
            Created InternalTransfer with calculated transfer price
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/finance/internal-transfers",
                json={
                    "origin_type": origin_type,
                    "volume_liters": volume_liters,
                    "unit_cost": unit_cost,
                    "source_reference": f"production_batch_{production_batch_id}",
                    "profit_center_from": profit_center_from,
                    "profit_center_to": profit_center_to
                }
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
