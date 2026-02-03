"""
Keg-related enums for asset management.
"""
from enum import Enum


class KegState(str, Enum):
    """
    Estados del Finite State Machine de barriles.
    
    Flow típico:
    EMPTY → DIRTY → CLEAN → FILLING → FULL → TAPPED/IN_CLIENT → EMPTY
    """
    EMPTY = "EMPTY"             # Vacío en planta
    DIRTY = "DIRTY"             # Sucio, requiere limpieza
    CLEAN = "CLEAN"             # Limpio, listo para llenar
    FILLING = "FILLING"         # En proceso de llenado
    FULL = "FULL"               # Lleno, listo para despacho
    TAPPED = "TAPPED"           # Conectado a grifo (taproom)
    IN_CLIENT = "IN_CLIENT"     # En posesión de cliente B2B
    IN_TRANSIT = "IN_TRANSIT"   # En tránsito
    QUARANTINE = "QUARANTINE"   # Cuarentena (QA issue)
    RETIRED = "RETIRED"         # Dado de baja (terminal state)


class KegSize(int, Enum):
    """Tamaños estándar de barriles en litros."""
    TWENTY = 20
    THIRTY = 30
    FIFTY = 50
    SIXTY = 60


class KegType(str, Enum):
    """Tipos de conexión de barril."""
    SANKE_D = "SANKE_D"         # Estándar comercial
    SANKE_S = "SANKE_S"         # Europeo
    CORNELIUS = "CORNELIUS"     # Homebrew
    OTHER = "OTHER"


class KegOwnership(str, Enum):
    """Tipo de propiedad del barril."""
    OWN = "OWN"                 # Propiedad de Desert Brew
    GUEST_BREWERY = "GUEST_BREWERY"  # De cervecería invitada
    RENTED = "RENTED"           # Rentado a proveedor
