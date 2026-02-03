"""
Logic package for Inventory Service business rules.
"""
from logic.stock_rotation import allocate_stock_fifo, InsufficientStockError

__all__ = ["allocate_stock_fifo", "InsufficientStockError"]
