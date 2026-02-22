"""
Client modules for inter-service communication.
"""
from .inventory_client import InventoryServiceClient, get_inventory_client
from .finance_client import FinanceServiceClient, get_finance_client

__all__ = [
    'InventoryServiceClient',
    'FinanceServiceClient',
    'get_inventory_client',
    'get_finance_client'
]
