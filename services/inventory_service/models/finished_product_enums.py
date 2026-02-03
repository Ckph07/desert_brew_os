"""
Finished Product Enums for Cold Room Inventory.
"""
from enum import Enum


class ProductType(str, Enum):
    """
    Type of finished product.
    
    - OWN_PRODUCTION: Cerveza producida en planta
    - COMMERCIAL: Cerveza comercial (Corona, Modelo, etc.)
    - GUEST_CRAFT: Cerveza de cervecería invitada
    - MERCHANDISE: Productos de merchandising
    """
    OWN_PRODUCTION = "OWN_PRODUCTION"
    COMMERCIAL = "COMMERCIAL"
    GUEST_CRAFT = "GUEST_CRAFT"
    MERCHANDISE = "MERCHANDISE"


class ProductCategory(str, Enum):
    """
    Category of finished product.
    
    Defines the packaging format and product type.
    """
    # Beer packaging
    BEER_KEG = "BEER_KEG"              # Barril (referencia al KegAsset)
    BEER_BOTTLE = "BEER_BOTTLE"        # Botellas (355ml, 940ml, etc.)
    BEER_CAN = "BEER_CAN"              # Latas (473ml típico)
    
    # Water packaging
    WATER_BOTTLE = "WATER_BOTTLE"      # Agua embotellada (500ml, 1L)
    WATER_JUG = "WATER_JUG"            # Garrafón (19L)
    
    # Merchandise
    MERCH_CAP = "MERCH_CAP"            # Cachucha
    MERCH_SHIRT = "MERCH_SHIRT"        # Playera
    MERCH_GLASS = "MERCH_GLASS"        # Vaso/Copa
    MERCH_GROWLER = "MERCH_GROWLER"    # Growler reutilizable
    MERCH_OTHER = "MERCH_OTHER"        # Otro merchandise


class AvailabilityStatus(str, Enum):
    """
    Availability status of finished product.
    
    Tracks if product is available for sale or reserved/allocated.
    """
    AVAILABLE = "AVAILABLE"      # Disponible para venta
    RESERVED = "RESERVED"        # Reservado para orden específica
    SOLD = "SOLD"                # Vendido (para historical tracking)
    DAMAGED = "DAMAGED"          # Dañado, no vendible
    EXPIRED = "EXPIRED"          # Vencido


class MovementType(str, Enum):
    """
    Type of product movement.
    
    Tracks how and why inventory changed.
    """
    PRODUCTION = "PRODUCTION"      # Ingreso desde producción
    PURCHASE = "PURCHASE"          # Compra (comercial/guest)
    SALE = "SALE"                  # Venta (decrease)
    TRANSFER = "TRANSFER"          # Transfer entre ubicaciones
    ADJUSTMENT = "ADJUSTMENT"      # Ajuste de inventario (conteo físico)
    DAMAGE = "DAMAGE"              # Baja por daño
    EXPIRATION = "EXPIRATION"      # Baja por vencimiento
    RETURN = "RETURN"              # Devolución de cliente


class ColdRoomLocation(str, Enum):
    """
    Pre-defined cold room locations.
    
    Desert Brew has 2 main cold rooms.
    """
    COLD_ROOM_A = "COLD_ROOM_A"    # Cuarto frío principal
    COLD_ROOM_B = "COLD_ROOM_B"    # Cuarto frío secundario
    TAPROOM_COOLER = "TAPROOM_COOLER"  # Refrigerador del taproom
    WAREHOUSE = "WAREHOUSE"         # Almacén (temperatura ambiente)
