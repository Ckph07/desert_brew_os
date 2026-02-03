"""
API package for Inventory Service.
"""
from api import stock_routes, movement_routes, supplier_routes, gas_routes, keg_routes, finished_product_routes

__all__ = [
    "stock_routes",
    "movement_routes",
    "supplier_routes",
    "gas_routes",
    "keg_routes",
    "finished_product_routes"
]
