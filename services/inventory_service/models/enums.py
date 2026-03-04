"""
Consolidated enums for Inventory Service.

Centralizes MovementType, MovementOrigin, and TransferStatus
used by stock_rotation.py and audit trail logic.
"""
import enum


class MovementType(str, enum.Enum):
    """Type of stock movement."""
    RECEIPT = "RECEIPT"           # Stock received from supplier
    CONSUMPTION = "CONSUMPTION"   # Stock consumed (production, sale, etc.)
    ADJUSTMENT = "ADJUSTMENT"     # Manual inventory adjustment
    TRANSFER = "TRANSFER"         # Transfer between locations
    RETURN = "RETURN"             # Returned stock
    LOSS = "LOSS"                 # Damaged/expired stock


class MovementOrigin(str, enum.Enum):
    """Origin/reason for the movement."""
    PURCHASE = "PURCHASE"         # Received from supplier purchase order
    PRODUCTION = "PRODUCTION"     # Consumed by a production batch
    SALE = "SALE"                 # Consumed by a sales order
    TRANSFER = "TRANSFER"         # Internal location transfer
    ADJUSTMENT = "ADJUSTMENT"     # Manual correction
    RETURN = "RETURN"             # Customer or production return
    WASTE = "WASTE"               # Spoilage / expired


class TransferStatus(str, enum.Enum):
    """Status of a stock transfer between locations."""
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
