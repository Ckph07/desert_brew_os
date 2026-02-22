"""
FastAPI routes for Ingredient Price reference CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from database import get_db
from models.ingredient_price import IngredientPrice
from schemas.cost_management import (
    IngredientPriceCreate,
    IngredientPriceUpdate,
    IngredientPriceResponse,
)

router = APIRouter(prefix="/api/v1/production/ingredients", tags=["Ingredient Prices"])


@router.post("", response_model=IngredientPriceResponse, status_code=201)
def create_ingredient_price(payload: IngredientPriceCreate, db: Session = Depends(get_db)):
    """Create an ingredient price entry."""
    ingredient = IngredientPrice(
        name=payload.name,
        category=payload.category.upper(),
        unit_measure=payload.unit_measure.upper(),
        current_price=payload.current_price,
        currency=payload.currency.upper(),
        supplier_name=payload.supplier_name,
        supplier_sku=payload.supplier_sku,
        notes=payload.notes,
        last_price_update=datetime.utcnow(),
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.get("", response_model=list[IngredientPriceResponse])
def list_ingredient_prices(
    category: Optional[str] = Query(None, description="MALT, HOP, YEAST, ADJUNCT, etc."),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
):
    """List ingredient prices with optional filters."""
    query = db.query(IngredientPrice)

    if active_only:
        query = query.filter(IngredientPrice.is_active == True)
    if category:
        query = query.filter(IngredientPrice.category == category.upper())
    if search:
        query = query.filter(IngredientPrice.name.ilike(f"%{search}%"))

    return query.order_by(IngredientPrice.category.asc(), IngredientPrice.name.asc()).all()


@router.get("/summary")
def get_ingredient_summary(db: Session = Depends(get_db)):
    """Get ingredient count and totals by category."""
    results = db.query(
        IngredientPrice.category,
        func.count(IngredientPrice.id).label("count"),
    ).filter(
        IngredientPrice.is_active == True,
    ).group_by(IngredientPrice.category).all()

    return {
        "categories": [
            {"category": r.category, "count": r.count}
            for r in results
        ],
        "total_ingredients": sum(r.count for r in results),
    }


@router.get("/{ingredient_id}", response_model=IngredientPriceResponse)
def get_ingredient_price(ingredient_id: int, db: Session = Depends(get_db)):
    """Get ingredient price details."""
    ingredient = db.query(IngredientPrice).filter(IngredientPrice.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient {ingredient_id} not found")
    return ingredient


@router.patch("/{ingredient_id}", response_model=IngredientPriceResponse)
def update_ingredient_price(
    ingredient_id: int,
    payload: IngredientPriceUpdate,
    db: Session = Depends(get_db),
):
    """Update an ingredient price."""
    ingredient = db.query(IngredientPrice).filter(IngredientPrice.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient {ingredient_id} not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Track price change timestamp
    if "current_price" in update_data:
        update_data["last_price_update"] = datetime.utcnow()

    for key, value in update_data.items():
        setattr(ingredient, key, value)

    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.delete("/{ingredient_id}", status_code=204)
def delete_ingredient_price(ingredient_id: int, db: Session = Depends(get_db)):
    """Soft-delete an ingredient price (sets is_active=False)."""
    ingredient = db.query(IngredientPrice).filter(IngredientPrice.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail=f"Ingredient {ingredient_id} not found")

    ingredient.is_active = False
    db.commit()
