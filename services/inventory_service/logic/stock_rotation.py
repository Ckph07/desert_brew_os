"""
Enhanced stock rotation with movement tracking and transfers.

Extends FIFO logic with audit trail and location transfers.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime
from models.stock import StockBatch
from models.movement import StockMovement
from models.transfer import StockTransfer
from models.enums import MovementType, MovementOrigin, TransferStatus


class InsufficientStockError(Exception):
    """Raised when there is not enough stock to fulfill allocation request."""
    
    def __init__(self, sku: str, requested: Decimal, available: Decimal):
        self.sku = sku
        self.requested = requested
        self.available = available
        super().__init__(
            f"Stock insuficiente para SKU '{sku}'. "
            f"Disponible: {available}, Requerido: {requested}"
        )


def log_movement(
    session: Session,
    batch_id: Optional[int],
    sku: str,
    movement_type: MovementType,
    quantity: Decimal,
    unit_measure: str,
    movement_origin: Optional[MovementOrigin] = None,
    from_location: Optional[str] = None,
    to_location: Optional[str] = None,
    reference: Optional[str] = None,
    notes: Optional[str] = None,
    created_by: Optional[str] = None,
    unit_cost: Optional[Decimal] = None,
) -> StockMovement:
    """
    Log a stock movement for audit trail.
    
    This creates a permanent record of what happened to the stock.
    """
    total_cost = (quantity * unit_cost) if unit_cost else None
    
    movement = StockMovement(
        batch_id=batch_id,
        sku=sku,
        movement_type=movement_type.value,
        movement_origin=movement_origin.value if movement_origin else None,
        quantity=quantity,
        unit_measure=unit_measure,
        from_location=from_location,
        to_location=to_location,
        unit_cost=unit_cost,
        total_cost=total_cost,
        reference=reference,
        notes=notes,
        created_by=created_by,
    )
    
    session.add(movement)
    return movement


def allocate_stock_fifo(
    sku: str,
    amount_needed: Decimal,
    session: Session,
    location: Optional[str] = None,
    movement_origin: Optional[MovementOrigin] = None,
    reference: Optional[str] = None,
    created_by: Optional[str] = None,
) -> List[Dict]:
    """
    Asigna stock usando el método FIFO (First-In, First-Out).
    
    ENHANCED: Now logs movements for audit trail.
    
    Args:
        sku: Código del producto
        amount_needed: Cantidad requerida
        session: SQLAlchemy session
        location: Optional location filter
        movement_origin: Why this allocation (PRODUCTION, SALE, etc.)
        reference: Reference number (e.g., "Production Order #42")
        created_by: Username who requested allocation
        
    Returns:
        Lista de asignaciones con batch_id y quantity
        
    Raises:
        InsufficientStockError: Si no hay suficiente stock disponible
    """
    # Build query with optional location filter
    stmt = (
        select(StockBatch)
        .where(
            StockBatch.sku == sku,
            StockBatch.remaining_quantity > 0
        )
        .order_by(StockBatch.arrival_date.asc())
        .with_for_update()
    )
    
    if location:
        stmt = stmt.where(StockBatch.location == location)
    
    batches = session.execute(stmt).scalars().all()
    
    # Validate total available
    total_available = sum(batch.remaining_quantity for batch in batches)
    
    if total_available < amount_needed:
        raise InsufficientStockError(
            sku=sku,
            requested=amount_needed,
            available=total_available
        )
    
    # Allocate from oldest batch
    allocations = []
    remaining = amount_needed
    
    for batch in batches:
        if remaining <= 0:
            break
        
        to_allocate = min(batch.remaining_quantity, remaining)
        
        # Update batch
        batch.remaining_quantity -= to_allocate
        if batch.remaining_quantity == 0:
            batch.is_allocated = True
        batch.lock_version += 1
        
        # Log movement for audit trail
        log_movement(
            session=session,
            batch_id=batch.id,
            sku=batch.sku,
            movement_type=MovementType.CONSUMPTION,
            quantity=to_allocate,
            unit_measure=batch.unit_measure,
            movement_origin=movement_origin,
            from_location=batch.location,
            reference=reference,
            created_by=created_by,
            unit_cost=batch.unit_cost,
        )
        
        # Record allocation
        allocations.append({
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "sku": batch.sku,
            "quantity": float(to_allocate),
            "unit_measure": batch.unit_measure,
            "unit_cost": float(batch.unit_cost),
            "total_cost": float(to_allocate * batch.unit_cost),
            "provider_name": batch.provider_name,
            "location": batch.location,
        })
        
        remaining -= to_allocate
    
    return allocations


def transfer_stock(
    sku: str,
    quantity: Decimal,
    from_location: str,
    to_location: str,
    session: Session,
    requested_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> StockTransfer:
    """
    Transfer stock from one location to another.
    
    Uses FIFO to allocate from origin, creates new batch at destination.
    
    Args:
        sku: Product SKU
        quantity: Amount to transfer
        from_location: Source location
        to_location: Destination location
        session: Database session
        requested_by: Who requested transfer
        notes: Optional notes
        
    Returns:
        StockTransfer record
        
    Raises:
        InsufficientStockError: If not enough stock at source location
    """
    # Create transfer record
    transfer = StockTransfer(
        sku=sku,
        quantity=quantity,
        unit_measure="",  # Will be set from first batch
        from_location=from_location,
        to_location=to_location,
        status=TransferStatus.PENDING.value,
        requested_by=requested_by,
        notes=notes,
    )
    session.add(transfer)
    session.flush()  # Get transfer.id
    
    # Allocate from source using FIFO
    allocations = allocate_stock_fifo(
        sku=sku,
        amount_needed=quantity,
        location=from_location,
        movement_origin=MovementOrigin.TRANSFER,
        reference=f"Transfer #{transfer.id}",
        created_by=requested_by,
        session=session,
    )
    
    # Set unit measure from first allocation
    if allocations:
        transfer.unit_measure = allocations[0]["unit_measure"]
    
    # Create new batch(es) at destination
    for alloc in allocations:
        new_batch = StockBatch(
            sku=sku,
            batch_number=f"TRANSFER-{transfer.id}-FROM-{alloc['batch_id']}",
            category=alloc.get("category", "OTHER"),
            initial_quantity=Decimal(str(alloc["quantity"])),
            remaining_quantity=Decimal(str(alloc["quantity"])),
            unit_measure=alloc["unit_measure"],
            unit_cost=Decimal(str(alloc["unit_cost"])),
            total_cost=Decimal(str(alloc["total_cost"])),
            location=to_location,
            provider_name=alloc.get("provider_name"),
        )
        session.add(new_batch)
        session.flush()
        
        # Log incoming movement at destination
        log_movement(
            session=session,
            batch_id=new_batch.id,
            sku=sku,
            movement_type=MovementType.TRANSFER,
            quantity=Decimal(str(alloc["quantity"])),
            unit_measure=alloc["unit_measure"],
            movement_origin=MovementOrigin.TRANSFER,
            from_location=from_location,
            to_location=to_location,
            reference=f"Transfer #{transfer.id}",
            created_by=requested_by,
            unit_cost=Decimal(str(alloc["unit_cost"])),
        )
    
    # Mark transfer as completed
    transfer.status = TransferStatus.COMPLETED.value
    transfer.completed_at = datetime.utcnow()
    transfer.executed_by = requested_by
    
    return transfer
