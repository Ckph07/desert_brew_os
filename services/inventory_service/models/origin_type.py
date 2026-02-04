"""
Product Origin Type Enum - WHO produces the product.

Critical for Transfer Pricing logic (Sprint 3.5).
"""
import enum


class OriginType(str, enum.Enum):
    """
    WHO produces the product (critical for Transfer Pricing).
    
    Business Rules:
    - HOUSE: Desert Brew factory production → Transfer Pricing (cost + 15%)
    - GUEST: Guest craft collaborations → Passthrough (0% factory margin)
    - COMMERCIAL: Commercial beers (Corona, Modelo) → Passthrough
    - MERCHANDISE: Non-beer products → Standard markup
    """
    HOUSE = "house"           # Producción propia (Desert Brew factory)
    GUEST = "guest"           # Cerveza guest craft (colaboraciones)
    COMMERCIAL = "commercial" # Cervezas comerciales (Corona, Modelo, etc.)
    MERCHANDISE = "merchandise" # Productos no-cerveza (merchandising)
