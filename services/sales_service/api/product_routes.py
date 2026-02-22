"""
FastAPI routes for Product Catalog CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.product_catalog import ProductCatalog
from models.price_history import PriceHistory
from schemas.product import (
    ProductCreate,
    ProductUpdate,
    ChannelPriceUpdate,
    ProductResponse,
    PriceHistoryResponse,
    MarginReportItem,
    MarginReportResponse,
)

router = APIRouter(prefix="/api/v1/sales/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product in the catalog."""
    # Check for duplicate SKU
    existing = db.query(ProductCatalog).filter(ProductCatalog.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{payload.sku}' already exists")

    product = ProductCatalog(**payload.model_dump(exclude_unset=False))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=list[ProductResponse])
def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    origin_type: Optional[str] = Query(None, description="Filter by origin: HOUSE, GUEST, COMMERCIAL"),
    active_only: bool = Query(True, description="Show only active products"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List products with optional filters."""
    query = db.query(ProductCatalog)

    if active_only:
        query = query.filter(ProductCatalog.is_active == True)
    if category:
        query = query.filter(ProductCatalog.category == category.upper())
    if origin_type:
        query = query.filter(ProductCatalog.origin_type == origin_type.upper())
    if search:
        query = query.filter(
            (ProductCatalog.product_name.ilike(f"%{search}%"))
            | (ProductCatalog.sku.ilike(f"%{search}%"))
        )

    products = query.order_by(ProductCatalog.product_name.asc()).offset(offset).limit(limit).all()
    return products


@router.get("/margin-report", response_model=MarginReportResponse)
def get_margin_report(
    category: Optional[str] = Query(None),
    origin_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Margin comparison report: fixed prices vs theoretical (OS-calculated) prices.

    Shows both margins side-by-side with delta percentage.
    """
    query = db.query(ProductCatalog).filter(ProductCatalog.is_active == True)

    if category:
        query = query.filter(ProductCatalog.category == category.upper())
    if origin_type:
        query = query.filter(ProductCatalog.origin_type == origin_type.upper())

    products = query.order_by(ProductCatalog.product_name.asc()).all()

    items = []
    fixed_margins = []
    theoretical_margins = []

    for p in products:
        fm = p.fixed_margin_pct
        tm = p.theoretical_margin_pct
        if fm is not None:
            fixed_margins.append(fm)
        if tm is not None:
            theoretical_margins.append(tm)

        items.append(MarginReportItem(
            id=p.id,
            sku=p.sku,
            product_name=p.product_name,
            category=p.category,
            origin_type=p.origin_type,
            cost_per_unit=float(p.cost_per_unit) if p.cost_per_unit else None,
            fixed_price=float(p.fixed_price) if p.fixed_price else None,
            theoretical_price=float(p.theoretical_price) if p.theoretical_price else None,
            fixed_margin_pct=fm,
            theoretical_margin_pct=tm,
            margin_delta_pct=p.margin_delta_pct,
            price_distributor=float(p.price_distributor) if p.price_distributor else None,
            price_taproom=float(p.price_taproom) if p.price_taproom else None,
        ))

    avg_fixed = round(sum(fixed_margins) / len(fixed_margins), 2) if fixed_margins else None
    avg_theoretical = round(sum(theoretical_margins) / len(theoretical_margins), 2) if theoretical_margins else None

    return MarginReportResponse(
        products=items,
        total_products=len(items),
        avg_fixed_margin=avg_fixed,
        avg_theoretical_margin=avg_theoretical,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details with margin calculations."""
    product = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    """Update a product."""
    product = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=200)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Soft-delete a product."""
    product = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    product.is_active = False
    db.commit()
    return {"message": f"Product '{product.sku}' deactivated", "product_id": product_id}


@router.patch("/{product_id}/prices", response_model=ProductResponse)
def update_channel_prices(
    product_id: int,
    payload: ChannelPriceUpdate,
    db: Session = Depends(get_db),
):
    """
    Update prices per channel with audit trail (PriceHistory).

    Every price change is logged to price_history table.
    """
    product = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    price_fields = {
        "price_taproom": "TAPROOM",
        "price_distributor": "DISTRIBUTOR",
        "price_on_premise": "ON_PREMISE",
        "price_off_premise": "OFF_PREMISE",
        "price_ecommerce": "ECOMMERCE",
        "fixed_price": "FIXED",
    }

    update_data = payload.model_dump(exclude_unset=True)

    for field, channel in price_fields.items():
        if field in update_data and update_data[field] is not None:
            old_val = getattr(product, field)
            new_val = update_data[field]

            # Log price change
            history = PriceHistory(
                product_id=product_id,
                channel=channel,
                old_price=old_val,
                new_price=new_val,
                change_reason=update_data.get("change_reason"),
                changed_by=update_data.get("changed_by"),
            )
            db.add(history)

            setattr(product, field, new_val)

    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}/price-history", response_model=list[PriceHistoryResponse])
def get_price_history(
    product_id: int,
    channel: Optional[str] = Query(None, description="Filter by channel"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get price change history for a product."""
    product = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    query = db.query(PriceHistory).filter(PriceHistory.product_id == product_id)

    if channel:
        query = query.filter(PriceHistory.channel == channel.upper())

    records = query.order_by(PriceHistory.changed_at.desc()).limit(limit).all()
    return records
