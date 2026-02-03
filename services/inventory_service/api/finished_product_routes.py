"""
API routes for Finished Product Inventory (Cold Room).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from database import get_db
from models.finished_product import FinishedProductInventory
from models.cold_room_reading import ColdRoomReading
from models.product_movement import ProductMovement
from models.finished_product_enums import (
    ProductType,
    ProductCategory,
    AvailabilityStatus,
    MovementType,
    ColdRoomLocation
)
from schemas.finished_product import (
    FinishedProductCreate,
    FinishedProductUpdate,
    FinishedProductResponse,
    FinishedProductWithMovements,
    ProductMovementCreate,
    ProductMovementResponse,
    ProductMoveRequest,
    ColdRoomReadingCreate,
    ColdRoomReadingResponse,
    ColdRoomStatusResponse,
    ColdRoomStatus,
    StockSummaryResponse,
    ProductTypeSummary,
    SlowMovingReportResponse,
    SlowMovingProduct
)

router = APIRouter()


# ==================== FINISHED PRODUCT CRUD ====================

@router.post("/finished-products", response_model=FinishedProductResponse, status_code=201)
def create_finished_product(
    product_data: FinishedProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new finished product in inventory.
    
    - OWN_PRODUCTION: Requires production_batch_id
    - COMMERCIAL/GUEST_CRAFT: Requires supplier_id
    - Auto-calculates total_cost from quantity * unit_cost
    """
    # Calculate total cost
    total_cost = None
    if product_data.unit_cost:
        total_cost = product_data.quantity * product_data.unit_cost
    
    # Create product
    product = FinishedProductInventory(
        sku=product_data.sku,
        product_name=product_data.product_name,
        product_type=product_data.product_type.value,
        category=product_data.category.value,
        production_batch_id=product_data.production_batch_id,
        supplier_id=product_data.supplier_id,
        guest_brewery_id=product_data.guest_brewery_id,
        keg_asset_id=product_data.keg_asset_id,
        quantity=product_data.quantity,
        unit_measure=product_data.unit_measure,
        cold_room_id=product_data.cold_room_id.value,
        shelf_position=product_data.shelf_position,
        unit_cost=product_data.unit_cost,
        total_cost=total_cost,
        production_date=product_data.production_date,
        best_before=product_data.best_before,
        notes=product_data.notes
    )
    
    db.add(product)
    db.flush()  # Generate ID before using it
    
    # Create initial movement log (PRODUCTION or PURCHASE)
    if product_data.product_type == ProductType.OWN_PRODUCTION:
        movement = ProductMovement.create_from_production(
            finished_product_id=product.id,
            quantity=product_data.quantity,
            production_batch_id=product_data.production_batch_id
        )
    else:
        movement = ProductMovement(
            finished_product_id=product.id,
            movement_type=MovementType.PURCHASE.value,
            quantity=product_data.quantity,
            to_location=product_data.cold_room_id.value,
            purchase_order_id=None,  # Can be added later
            notes=f"Initial stock of {product_data.product_name}"
        )
    
    db.add(movement)
    db.commit()
    db.refresh(product)
    
    return product


@router.get("/finished-products", response_model=List[FinishedProductResponse])
def list_finished_products(
    product_type: Optional[ProductType] = None,
    category: Optional[ProductCategory] = None,
    cold_room_id: Optional[ColdRoomLocation] = None,
    availability_status: Optional[AvailabilityStatus] = None,
    production_batch_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List finished products with optional filters.
    
    Filters:
    - product_type: OWN_PRODUCTION, COMMERCIAL, GUEST_CRAFT, MERCHANDISE
    - category: BEER_KEG, BEER_BOTTLE, etc.
    - cold_room_id: Location filter
    - availability_status: AVAILABLE, RESERVED, SOLD, etc.
    - production_batch_id: Filter by production batch
    - supplier_id: Filter by supplier
    """
    query = db.query(FinishedProductInventory)
    
    if product_type:
        query = query.filter(FinishedProductInventory.product_type == product_type.value)
    
    if category:
        query = query.filter(FinishedProductInventory.category == category.value)
    
    if cold_room_id:
        query = query.filter(FinishedProductInventory.cold_room_id == cold_room_id.value)
    
    if availability_status:
        query = query.filter(FinishedProductInventory.availability_status == availability_status.value)
    
    if production_batch_id:
        query = query.filter(FinishedProductInventory.production_batch_id == production_batch_id)
    
    if supplier_id:
        query = query.filter(FinishedProductInventory.supplier_id == supplier_id)
    
    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/finished-products/summary", response_model=StockSummaryResponse)
def get_stock_summary(db: Session = Depends(get_db)):
    """
    Get stock summary by product type and category.
    
    Returns total quantities and values for each type/category combination.
    """
    summary = {
        "own_production": {},
        "commercial": {},
        "guest_craft": {},
        "merchandise": {},
        "total_items": Decimal('0.00'),
        "total_value": Decimal('0.00')
    }
    
    # Query aggregation by type and category
    results = db.query(
        FinishedProductInventory.product_type,
        FinishedProductInventory.category,
        func.sum(FinishedProductInventory.quantity).label('total_quantity'),
        func.sum(FinishedProductInventory.total_cost).label('total_value')
    ).filter(
        FinishedProductInventory.availability_status == AvailabilityStatus.AVAILABLE.value
    ).group_by(
        FinishedProductInventory.product_type,
        FinishedProductInventory.category
    ).all()
    
    for product_type, category, qty, value in results:
        type_key = product_type.lower()
        
        if type_key not in summary:
            type_key = "own_production"  # Fallback
        
        summary[type_key][category] = ProductTypeSummary(
            quantity=Decimal(qty or 0),
            value=Decimal(value or 0)
        )
        
        summary["total_items"] += Decimal(qty or 0)
        summary["total_value"] += Decimal(value or 0)
    
    return summary


@router.get("/finished-products/slow-moving", response_model=SlowMovingReportResponse)
def get_slow_moving_products(
    days_threshold: int = Query(30, ge=1, le=365, description="Days without movement"),
    db: Session = Depends(get_db)
):
    """
    Get products with no movements in X days.
    
    Useful for identifying stale inventory that needs promotion or clearance.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
    
    # Subquery: last movement per product
    last_movement_subq = db.query(
        ProductMovement.finished_product_id,
        func.max(ProductMovement.timestamp).label("last_movement")
    ).group_by(ProductMovement.finished_product_id).subquery()
    
    # Products with old or no movements
    products = db.query(
        FinishedProductInventory,
        last_movement_subq.c.last_movement
    ).outerjoin(
        last_movement_subq,
        FinishedProductInventory.id == last_movement_subq.c.finished_product_id
    ).filter(
        and_(
            FinishedProductInventory.availability_status == AvailabilityStatus.AVAILABLE.value,
            FinishedProductInventory.quantity > 0,
            or_(
                last_movement_subq.c.last_movement < cutoff_date,
                last_movement_subq.c.last_movement.is_(None)
            )
        )
    ).all()
    
    slow_products = []
    total_value_at_risk = Decimal('0.00')
    
    for product, last_movement in products:
        days_without = None
        if last_movement:
            days_without = (datetime.utcnow() - last_movement).days
        
        slow_products.append(SlowMovingProduct(
            id=product.id,
            sku=product.sku,
            product_name=product.product_name,
            category=product.category,
            quantity=product.quantity,
            cold_room_id=product.cold_room_id,
            last_movement=last_movement,
            days_without_movement=days_without,
            value=product.value
        ))
        
        total_value_at_risk += product.value
    
    return SlowMovingReportResponse(
        products=slow_products,
        total_value_at_risk=total_value_at_risk
    )


@router.get("/finished-products/own", response_model=List[FinishedProductResponse])
def get_own_production_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get only own production beer products.
    
    Shortcut for filtering by OWN_PRODUCTION type.
    """
    products = db.query(FinishedProductInventory).filter(
        FinishedProductInventory.product_type == ProductType.OWN_PRODUCTION.value
    ).offset(skip).limit(limit).all()
    
    return products


@router.get("/finished-products/{product_id}", response_model=FinishedProductWithMovements)
def get_finished_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get finished product detail with movement history.
    
    Includes complete audit trail of all movements.
    """
    product = db.query(FinishedProductInventory).filter(
        FinishedProductInventory.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get movement history
    movements = db.query(ProductMovement).filter(
        ProductMovement.finished_product_id == product_id
    ).order_by(ProductMovement.timestamp.desc()).all()
    
    return {
        **product.__dict__,
        "movements": movements
    }


@router.patch("/finished-products/{product_id}", response_model=FinishedProductResponse)
def update_finished_product(
    product_id: int,
    product_update: FinishedProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update finished product (location, status).
    
    Use /move endpoint for quantity changes with audit trail.
    """
    product = db.query(FinishedProductInventory).filter(
        FinishedProductInventory.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Apply updates
    if product_update.cold_room_id is not None:
        # Create transfer movement if location changes
        if product.cold_room_id != product_update.cold_room_id.value:
            transfer = ProductMovement(
                finished_product_id=product_id,
                movement_type=MovementType.TRANSFER.value,
                quantity=product.quantity,
                from_location=product.cold_room_id,
                to_location=product_update.cold_room_id.value,
                notes=product_update.notes or "Location transfer"
            )
            db.add(transfer)
        
        product.cold_room_id = product_update.cold_room_id.value
    
    if product_update.shelf_position is not None:
        product.shelf_position = product_update.shelf_position
    
    if product_update.availability_status is not None:
        product.availability_status = product_update.availability_status.value
    
    if product_update.notes is not None:
        product.notes = product_update.notes
    
    product.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(product)
    
    return product


# ==================== PRODUCT MOVEMENTS ====================

@router.post("/finished-products/{product_id}/move", response_model=ProductMovementResponse)
def move_product(
    product_id: int,
    move_req: ProductMoveRequest,
    db: Session = Depends(get_db)
):
    """
    Move product quantity to another location.
    
    Creates audit trail via ProductMovement.
    Can be used for partial moves (splitting inventory).
    """
    product = db.query(FinishedProductInventory).filter(
        FinishedProductInventory.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate quantity
    if move_req.quantity > product.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move {move_req.quantity} (available: {product.quantity})"
        )
    
    # Create movement log
    movement = ProductMovement(
        finished_product_id=product_id,
        movement_type=MovementType.TRANSFER.value,
        quantity=move_req.quantity,
        from_location=product.cold_room_id,
        to_location=move_req.to_location.value,
        user_id=move_req.user_id,
        notes=move_req.notes
    )
    
    # If moving ALL quantity, update product location
    if move_req.quantity == product.quantity:
        product.cold_room_id = move_req.to_location.value
        if move_req.to_shelf:
            product.shelf_position = move_req.to_shelf
        product.updated_at = datetime.utcnow()
    else:
        # Partial move: create new product entry at destination
        # (Keep original, create split inventory)
        new_product = FinishedProductInventory(
            sku=product.sku,
            product_name=product.product_name,
            product_type=product.product_type,
            category=product.category,
            production_batch_id=product.production_batch_id,
            supplier_id=product.supplier_id,
            guest_brewery_id=product.guest_brewery_id,
            quantity=move_req.quantity,
            unit_measure=product.unit_measure,
            cold_room_id=move_req.to_location.value,
            shelf_position=move_req.to_shelf,
            unit_cost=product.unit_cost,
            total_cost=move_req.quantity * (product.unit_cost or Decimal('0.00')),
            production_date=product.production_date,
            best_before=product.best_before,
            notes=f"Split from product {product_id}"
        )
        
        # Reduce original quantity
        product.update_quantity(-move_req.quantity)
        
        db.add(new_product)
    
    db.add(movement)
    db.commit()
    db.refresh(movement)
    
    return movement


# ==================== REPORTS ====================
# Note: Specific routes moved before /{product_id} to prevent path conflicts


# ==================== COLD ROOM MONITORING ====================

@router.post("/cold-room/readings", response_model=ColdRoomReadingResponse, status_code=201)
def create_cold_room_reading(
    reading_data: ColdRoomReadingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new temperature/humidity reading for cold room.
    
    Automatically checks for alerts:
    - Temperature > 7°C or < 0°C
    - Humidity > 80%
    """
    reading = ColdRoomReading.create_reading(
        cold_room_id=reading_data.cold_room_id.value,
        temperature=reading_data.temperature_celsius,
        humidity=reading_data.humidity_percent
    )
    
    db.add(reading)
    db.commit()
    db.refresh(reading)
    
    # TODO: If alert triggered, send notification (webhook, email, etc.)
    
    return reading


@router.get("/cold-room/status", response_model=ColdRoomStatusResponse)
def get_cold_room_status(db: Session = Depends(get_db)):
    """
    Get current status of all cold rooms.
    
    Returns latest reading, alert status, and utilization.
    """
    cold_rooms_status = []
    
    for room in ColdRoomLocation:
        # Get latest reading
        latest_reading = db.query(ColdRoomReading).filter(
            ColdRoomReading.cold_room_id == room.value
        ).order_by(ColdRoomReading.timestamp.desc()).first()
        
        if not latest_reading:
            continue
        
        # Check for active alerts (last 30 minutes)
        recent_alert = db.query(ColdRoomReading).filter(
            and_(
                ColdRoomReading.cold_room_id == room.value,
                ColdRoomReading.alert_triggered == True,
                ColdRoomReading.timestamp >= datetime.utcnow() - timedelta(minutes=30)
            )
        ).first()
        
        cold_rooms_status.append(ColdRoomStatus(
            id=room.value,
            current_temp=latest_reading.temperature_celsius,
            last_reading=latest_reading.timestamp,
            alert_active=recent_alert is not None
        ))
    
    return ColdRoomStatusResponse(cold_rooms=cold_rooms_status)
