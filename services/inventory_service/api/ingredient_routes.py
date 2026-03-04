"""
API routes for ingredient catalog management.
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.ingredient_catalog import IngredientCatalogItem
from schemas.ingredient import (
    IngredientCatalogCreate,
    IngredientCatalogResponse,
    IngredientCatalogUpdate,
)

router = APIRouter()


def _normalize_sku(name_or_sku: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "-", name_or_sku.strip().upper())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "UNKNOWN"


@router.post("/ingredients", response_model=IngredientCatalogResponse, status_code=201)
async def create_ingredient(
    payload: IngredientCatalogCreate,
    db: Session = Depends(get_db),
):
    """Create an ingredient catalog item."""
    sku = payload.sku or _normalize_sku(payload.name)

    exists = db.execute(
        select(IngredientCatalogItem).where(IngredientCatalogItem.sku == sku)
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"Ingredient with SKU '{sku}' already exists",
        )

    ingredient = IngredientCatalogItem(
        sku=sku,
        name=payload.name,
        category=payload.category.value,
        default_unit=payload.unit_measure.value,
        notes=payload.notes,
        is_active=True,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return IngredientCatalogResponse(
        id=ingredient.id,
        sku=ingredient.sku,
        name=ingredient.name,
        category=ingredient.category,
        unit_measure=ingredient.default_unit,
        notes=ingredient.notes,
        is_active=ingredient.is_active,
        created_at=ingredient.created_at,
        updated_at=ingredient.updated_at,
    )


@router.get("/ingredients", response_model=list[IngredientCatalogResponse])
async def list_ingredients(
    active_only: bool = Query(True, description="Only show active ingredients"),
    search: Optional[str] = Query(None, description="Filter by sku/name/category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List ingredient catalog items with optional filters."""
    query = select(IngredientCatalogItem)

    if active_only:
        query = query.where(IngredientCatalogItem.is_active.is_(True))

    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            IngredientCatalogItem.sku.ilike(pattern)
            | IngredientCatalogItem.name.ilike(pattern)
            | IngredientCatalogItem.category.ilike(pattern)
        )

    query = query.order_by(IngredientCatalogItem.name.asc()).offset(skip).limit(limit)
    items = db.execute(query).scalars().all()

    return [
        IngredientCatalogResponse(
            id=item.id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            unit_measure=item.default_unit,
            notes=item.notes,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]


@router.get("/ingredients/{ingredient_id}", response_model=IngredientCatalogResponse)
async def get_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Get a single ingredient catalog item."""
    ingredient = db.get(IngredientCatalogItem, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=404,
            detail=f"Ingredient with id {ingredient_id} not found",
        )

    return IngredientCatalogResponse(
        id=ingredient.id,
        sku=ingredient.sku,
        name=ingredient.name,
        category=ingredient.category,
        unit_measure=ingredient.default_unit,
        notes=ingredient.notes,
        is_active=ingredient.is_active,
        created_at=ingredient.created_at,
        updated_at=ingredient.updated_at,
    )


@router.patch("/ingredients/{ingredient_id}", response_model=IngredientCatalogResponse)
async def update_ingredient(
    ingredient_id: int,
    payload: IngredientCatalogUpdate,
    db: Session = Depends(get_db),
):
    """Update an ingredient catalog item."""
    ingredient = db.get(IngredientCatalogItem, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=404,
            detail=f"Ingredient with id {ingredient_id} not found",
        )

    data = payload.model_dump(exclude_unset=True)

    if "sku" in data and data["sku"]:
        next_sku = data["sku"].upper()
        if next_sku != ingredient.sku:
            exists = db.execute(
                select(IngredientCatalogItem).where(
                    IngredientCatalogItem.sku == next_sku
                )
            ).scalar_one_or_none()
            if exists:
                raise HTTPException(
                    status_code=409,
                    detail=f"Ingredient with SKU '{next_sku}' already exists",
                )
            ingredient.sku = next_sku

    if "name" in data and data["name"] is not None:
        ingredient.name = data["name"]
    if "category" in data and data["category"] is not None:
        ingredient.category = data["category"].value
    if "unit_measure" in data and data["unit_measure"] is not None:
        ingredient.default_unit = data["unit_measure"].value
    if "notes" in data:
        ingredient.notes = data["notes"]
    if "is_active" in data and data["is_active"] is not None:
        ingredient.is_active = data["is_active"]

    db.commit()
    db.refresh(ingredient)

    return IngredientCatalogResponse(
        id=ingredient.id,
        sku=ingredient.sku,
        name=ingredient.name,
        category=ingredient.category,
        unit_measure=ingredient.default_unit,
        notes=ingredient.notes,
        is_active=ingredient.is_active,
        created_at=ingredient.created_at,
        updated_at=ingredient.updated_at,
    )


@router.delete("/ingredients/{ingredient_id}")
async def deactivate_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
):
    """Soft-delete ingredient catalog item."""
    ingredient = db.get(IngredientCatalogItem, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=404,
            detail=f"Ingredient with id {ingredient_id} not found",
        )

    ingredient.is_active = False
    db.commit()

    return {
        "message": f"Ingredient '{ingredient.name}' deactivated successfully",
        "id": ingredient_id,
    }
