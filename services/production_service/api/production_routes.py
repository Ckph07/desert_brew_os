"""
Production Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import tempfile
import os
import httpx
from datetime import datetime
import re

from database import get_db
from models.recipe import Recipe
from models.production_batch import ProductionBatch, BatchStatus
from models.batch_ingredient_allocation import BatchIngredientAllocation
from schemas.production import (
    RecipeResponse,
    CreateRecipeRequest,
    UpdateRecipeRequest,
    CreateBatchRequest,
    BatchResponse,
    BatchDetailResponse,
    UpdateBatchVolumeRequest,
    CancelBatchRequest,
    CostBreakdownResponse,
    BatchTransitionResponse,
    RecipeInventoryValidationRequest,
    RecipeInventoryValidationResponse,
    RecipeInventoryValidationItem,
)
from logic.beersmith_parser import BeerSmithParser
from logic.batch_state_machine import BatchStateMachine
from logic.cost_allocator import CostAllocator
from clients.inventory_client import InventoryServiceClient, get_inventory_client
from clients.finance_client import FinanceServiceClient, get_finance_client
from events.publisher import EventPublisher, get_event_publisher
from exceptions import InsufficientStockError, ServiceUnavailableError

router = APIRouter(prefix="/api/v1/production", tags=["Production"])


class _RecipeAllocationView:
    """Lightweight recipe view used by CostAllocator."""

    def __init__(
        self,
        batch_size_liters: float,
        fermentables: List[Dict[str, Any]],
        hops: List[Dict[str, Any]],
        yeast: List[Dict[str, Any]],
    ):
        self.batch_size_liters = batch_size_liters
        self.fermentables = fermentables
        self.hops = hops
        self.yeast = yeast


def _copy_dict_list(items: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Create a defensive copy for JSON list fields."""
    if not isinstance(items, list):
        return []
    return [dict(item) for item in items if isinstance(item, dict)]


def _normalize_sku(value: str) -> str:
    """Normalize ingredient names to SKU-friendly tokens."""
    normalized = re.sub(r"[^A-Z0-9]+", "-", value.strip().upper())
    return normalized.strip("-")


def _ensure_recipe_sku_fields(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure every ingredient row has a `sku` key."""
    normalized: List[Dict[str, Any]] = []
    for item in items:
        row = dict(item)
        sku = row.get("sku")
        if isinstance(sku, str):
            sku = _normalize_sku(sku)
        if not sku:
            name = row.get("name")
            if isinstance(name, str) and name.strip():
                sku = _normalize_sku(name)
        row["sku"] = sku
        normalized.append(row)
    return normalized


def _apply_recipe_normalization(recipe: Recipe) -> None:
    """Normalize ingredient payload before saving recipe."""
    recipe.fermentables = _ensure_recipe_sku_fields(_copy_dict_list(recipe.fermentables))
    recipe.hops = _ensure_recipe_sku_fields(_copy_dict_list(recipe.hops))
    recipe.yeast = _ensure_recipe_sku_fields(_copy_dict_list(recipe.yeast))


def _build_recipe_snapshot(recipe: Recipe) -> Dict[str, Any]:
    """Capture immutable recipe payload at batch planning time."""
    return {
        "source_recipe_id": recipe.id,
        "name": recipe.name,
        "style": recipe.style,
        "brewer": recipe.brewer,
        "batch_size_liters": float(recipe.batch_size_liters),
        "fermentables": _copy_dict_list(recipe.fermentables),
        "hops": _copy_dict_list(recipe.hops),
        "yeast": _copy_dict_list(recipe.yeast),
        "water_profile": dict(recipe.water_profile) if isinstance(recipe.water_profile, dict) else None,
        "mash_steps": _copy_dict_list(recipe.mash_steps),
        "expected_og": float(recipe.expected_og) if recipe.expected_og is not None else None,
        "expected_fg": float(recipe.expected_fg) if recipe.expected_fg is not None else None,
        "expected_abv": float(recipe.expected_abv) if recipe.expected_abv is not None else None,
        "ibu": float(recipe.ibu) if recipe.ibu is not None else None,
        "color_srm": float(recipe.color_srm) if recipe.color_srm is not None else None,
        "brewhouse_efficiency": (
            float(recipe.brewhouse_efficiency) if recipe.brewhouse_efficiency is not None else None
        ),
        "notes": recipe.notes,
        "captured_at": datetime.utcnow().isoformat(),
    }


def _resolve_recipe_for_allocation(
    batch: ProductionBatch,
    fallback_recipe: Optional[Recipe],
) -> Optional[_RecipeAllocationView]:
    """Resolve recipe payload for costing, preferring immutable batch snapshot."""
    snapshot = batch.recipe_snapshot if isinstance(batch.recipe_snapshot, dict) else {}

    if snapshot:
        batch_size_liters = snapshot.get("batch_size_liters")
        if batch_size_liters is None:
            if fallback_recipe is not None:
                batch_size_liters = float(fallback_recipe.batch_size_liters)
            else:
                batch_size_liters = float(batch.planned_volume_liters)

        fermentables = _copy_dict_list(snapshot.get("fermentables")) or _copy_dict_list(
            getattr(fallback_recipe, "fermentables", [])
        )
        hops = _copy_dict_list(snapshot.get("hops")) or _copy_dict_list(
            getattr(fallback_recipe, "hops", [])
        )
        yeast = _copy_dict_list(snapshot.get("yeast")) or _copy_dict_list(
            getattr(fallback_recipe, "yeast", [])
        )

        return _RecipeAllocationView(
            batch_size_liters=float(batch_size_liters),
            fermentables=fermentables,
            hops=hops,
            yeast=yeast,
        )

    if fallback_recipe is None:
        return None

    return _RecipeAllocationView(
        batch_size_liters=float(fallback_recipe.batch_size_liters),
        fermentables=_copy_dict_list(fallback_recipe.fermentables),
        hops=_copy_dict_list(fallback_recipe.hops),
        yeast=_copy_dict_list(fallback_recipe.yeast),
    )


# =====================
# Recipe Endpoints (6)
# =====================

@router.post("/recipes", response_model=RecipeResponse, status_code=201)
def create_recipe_manual(
    payload: CreateRecipeRequest,
    db: Session = Depends(get_db)
):
    """
    Create a recipe manually (without BeerSmith .bsmx file).

    Accepts full recipe definition as JSON.
    """
    recipe = Recipe(
        name=payload.name,
        style=payload.style,
        brewer=payload.brewer,
        batch_size_liters=payload.batch_size_liters,
        fermentables=[f.model_dump() for f in payload.fermentables],
        hops=[h.model_dump() for h in payload.hops],
        yeast=[y.model_dump() for y in payload.yeast],
        water_profile=payload.water_profile,
        mash_steps=[m.model_dump() for m in payload.mash_steps] if payload.mash_steps else None,
        expected_og=payload.expected_og,
        expected_fg=payload.expected_fg,
        expected_abv=payload.expected_abv,
        ibu=payload.ibu,
        color_srm=payload.color_srm,
        brewhouse_efficiency=payload.brewhouse_efficiency,
        notes=payload.notes,
    )
    _apply_recipe_normalization(recipe)

    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe

@router.post("/recipes/import", response_model=RecipeResponse, status_code=201)
async def import_beersmith_recipe(
    file: UploadFile = File(..., description=".bsmx file from BeerSmith"),
    user_id: int = Query(None, description="User importing recipe"),
    db: Session = Depends(get_db)
):
    """
    Import BeerSmith recipe from .bsmx file.
    
    Parses XML and creates Recipe in database.
    """
    if not file.filename.endswith('.bsmx'):
        raise HTTPException(400, "File must be .bsmx format")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bsmx') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Parse recipe
        recipe = BeerSmithParser.parse_file(tmp_path)
        recipe.imported_by_user_id = user_id
        _apply_recipe_normalization(recipe)
        
        # Save to database
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        
        return recipe
        
    except Exception as e:
        raise HTTPException(400, f"Failed to parse recipe: {str(e)}")
        
    finally:
        # Clean up temp file
        os.unlink(tmp_path)


@router.get("/recipes", response_model=List[RecipeResponse])
def list_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List all recipes."""
    recipes = db.query(Recipe).order_by(Recipe.imported_at.desc()).offset(skip).limit(limit).all()
    return recipes


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get recipe details."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, f"Recipe {recipe_id} not found")
    return recipe


@router.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Delete recipe."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, f"Recipe {recipe_id} not found")
    
    # Check if recipe is used by any batches
    batch_count = db.query(ProductionBatch).filter(ProductionBatch.recipe_id == recipe_id).count()
    if batch_count > 0:
        raise HTTPException(400, f"Cannot delete recipe used by {batch_count} batches")
    
    db.delete(recipe)
    db.commit()


@router.patch("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: int,
    payload: UpdateRecipeRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing recipe.

    Only fields provided will be updated.
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, f"Recipe {recipe_id} not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Convert Pydantic sub-models to dicts for JSON columns
    if "fermentables" in update_data and update_data["fermentables"] is not None:
        update_data["fermentables"] = [f.model_dump() for f in payload.fermentables]
    if "hops" in update_data and update_data["hops"] is not None:
        update_data["hops"] = [h.model_dump() for h in payload.hops]
    if "yeast" in update_data and update_data["yeast"] is not None:
        update_data["yeast"] = [y.model_dump() for y in payload.yeast]
    if "mash_steps" in update_data and update_data["mash_steps"] is not None:
        update_data["mash_steps"] = [m.model_dump() for m in payload.mash_steps]

    for key, value in update_data.items():
        setattr(recipe, key, value)
    _apply_recipe_normalization(recipe)

    db.commit()
    db.refresh(recipe)
    return recipe


# ===========================
# Production Batch Endpoints (8)
# ===========================

@router.post("/batches", response_model=BatchDetailResponse, status_code=201)
def create_batch(
    batch_req: CreateBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Create new production batch (PLANNED status).
    """
    # Validate recipe exists
    recipe = db.query(Recipe).filter(Recipe.id == batch_req.recipe_id).first()
    if not recipe:
        raise HTTPException(404, f"Recipe {batch_req.recipe_id} not found")
    
    # Check batch number uniqueness
    existing = db.query(ProductionBatch).filter(ProductionBatch.batch_number == batch_req.batch_number).first()
    if existing:
        raise HTTPException(409, f"Batch number '{batch_req.batch_number}' already exists")
    
    # Create batch
    batch = ProductionBatch(
        batch_number=batch_req.batch_number,
        recipe_id=batch_req.recipe_id,
        recipe_name=recipe.name,
        recipe_snapshot=_build_recipe_snapshot(recipe),
        planned_volume_liters=batch_req.planned_volume_liters,
        status=BatchStatus.PLANNED.value,
        notes=batch_req.notes,
        created_by_user_id=batch_req.created_by_user_id
    )
    
    db.add(batch)
    db.commit()
    db.refresh(batch)
    
    return batch


@router.get("/batches", response_model=List[BatchResponse])
def list_batches(
    status: str = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List

 production batches."""
    query = db.query(ProductionBatch)
    
    if status:
        query = query.filter(ProductionBatch.status == status)
    
    batches = query.order_by(ProductionBatch.planned_at.desc()).offset(skip).limit(limit).all()
    return batches


@router.get("/batches/{batch_id}", response_model=BatchDetailResponse)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    """Get batch details with cost breakdown."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    return batch


@router.patch("/batches/{batch_id}/start-brewing", response_model=BatchTransitionResponse)
async def start_brewing(
    batch_id: int,
    inventory_client: InventoryServiceClient = Depends(get_inventory_client),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    db: Session = Depends(get_db)
):
    """
    Transition batch: PLANNED → BREWING and allocate costs via real FIFO.
    
    Sprint 4.5: Uses real Inventory Service StockBatch for FIFO allocation.
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    previous_status = batch.status
    
    # Transition state
    try:
        BatchStateMachine.transition(batch, BatchStatus.BREWING, notes="Started brewing")
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # Allocate costs via real FIFO from Inventory Service
    recipe = db.query(Recipe).filter(Recipe.id == batch.recipe_id).first()
    recipe_for_allocation = _resolve_recipe_for_allocation(batch, recipe)
    if recipe_for_allocation is None:
        raise HTTPException(
            404,
            f"Recipe {batch.recipe_id} not found and batch has no recipe snapshot",
        )
    
    try:
        cost_breakdown = await CostAllocator.allocate_batch_costs(
            batch=batch,
            recipe=recipe_for_allocation,
            db=db,
            inventory_client=inventory_client
        )
    except InsufficientStockError as e:
        db.rollback()
        raise HTTPException(
            400,
            f"Insufficient stock: {e.ingredient} (required: {e.required}{e.unit}, available: {e.available}{e.unit})"
        )
    except ServiceUnavailableError as e:
        db.rollback()
        raise HTTPException(503, f"Service unavailable: {e.service_name}")
    except httpx.HTTPError as e:
        db.rollback()
        raise HTTPException(503, f"Inventory Service error: {str(e)}")
    
    db.commit()
    
    # Publish event to RabbitMQ
    try:
        event_publisher.publish(
            routing_key="production.batch_started",
            message={
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "recipe_id": batch.recipe_id,
                "recipe_name": batch.recipe_name,
                "planned_volume_liters": float(batch.planned_volume_liters),
                "total_cost": float(batch.total_cost),
                "cost_breakdown": cost_breakdown
            }
        )
    except Exception as e:
        # Don't fail the request if event publishing fails
        print(f"Warning: Failed to publish batch_started event: {e}")
    
    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.brewing_started_at,
        message=f"Batch started brewing. Total cost allocated: ${batch.total_cost} ({cost_breakdown['allocations_count']} allocations)"
    )


@router.patch("/batches/{batch_id}/start-fermenting", response_model=BatchTransitionResponse)
def start_fermenting(batch_id: int, db: Session = Depends(get_db)):
    """Transition: BREWING → FERMENTING."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    previous_status = batch.status
    
    try:
        BatchStateMachine.transition(batch, BatchStatus.FERMENTING)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    db.commit()
    
    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.fermenting_started_at,
        message="Batch moved to fermenter"
    )


@router.patch("/batches/{batch_id}/start-conditioning", response_model=BatchTransitionResponse)
def start_conditioning(batch_id: int, db: Session = Depends(get_db)):
    """Transition: FERMENTING → CONDITIONING."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")

    previous_status = batch.status

    try:
        BatchStateMachine.transition(batch, BatchStatus.CONDITIONING)
    except ValueError as e:
        raise HTTPException(400, str(e))

    db.commit()

    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.conditioning_started_at,
        message="Batch moved to conditioning"
    )


@router.patch("/batches/{batch_id}/start-packaging", response_model=BatchTransitionResponse)
def start_packaging(batch_id: int, db: Session = Depends(get_db)):
    """Transition: FERMENTING/CONDITIONING → PACKAGING."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")

    previous_status = batch.status

    try:
        BatchStateMachine.transition(batch, BatchStatus.PACKAGING)
    except ValueError as e:
        raise HTTPException(400, str(e))

    db.commit()

    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.packaging_started_at,
        message="Batch moved to packaging"
    )


@router.patch("/batches/{batch_id}/cancel", response_model=BatchTransitionResponse)
def cancel_batch(
    batch_id: int,
    payload: CancelBatchRequest,
    db: Session = Depends(get_db),
):
    """Transition batch to CANCELLED with optional reason."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")

    previous_status = batch.status
    reason = payload.reason or "Cancelled from frontend"

    try:
        BatchStateMachine.transition(batch, BatchStatus.CANCELLED, notes=reason)
    except ValueError as e:
        raise HTTPException(400, str(e))

    db.commit()

    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.cancelled_at,
        message=f"Batch cancelled: {reason}",
    )


@router.post(
    "/recipes/{recipe_id}/validate-stock",
    response_model=RecipeInventoryValidationResponse,
)
async def validate_recipe_stock(
    recipe_id: int,
    payload: RecipeInventoryValidationRequest,
    inventory_client: InventoryServiceClient = Depends(get_inventory_client),
    db: Session = Depends(get_db),
):
    """
    Validate recipe ingredients against available inventory before brewing.

    Uses SKU when present in recipe ingredients, fallback to ingredient name.
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(404, f"Recipe {recipe_id} not found")

    _apply_recipe_normalization(recipe)

    base_volume = float(recipe.batch_size_liters)
    planned_volume = float(payload.planned_volume_liters or base_volume)
    scale_factor = planned_volume / base_volume if base_volume > 0 else 1.0

    items: List[RecipeInventoryValidationItem] = []

    async def _check_item(
        ingredient_type: str,
        name: str,
        sku: Optional[str],
        required_quantity: float,
        unit: str,
    ) -> None:
        lookup_key = sku or name
        if not lookup_key:
            items.append(
                RecipeInventoryValidationItem(
                    ingredient_type=ingredient_type,
                    name=name or "UNKNOWN",
                    sku=sku,
                    lookup_key="",
                    required_quantity=required_quantity,
                    unit=unit,
                    available_quantity=0.0,
                    status="MISSING",
                    matched_batches=0,
                )
            )
            return

        try:
            stock_batches = await inventory_client.get_available_stock_batches(
                ingredient_name=lookup_key,
                min_quantity=0.0,
            )
        except httpx.HTTPError as e:
            raise HTTPException(503, f"Inventory Service error: {str(e)}")

        available = sum(float(batch.get("available_quantity", 0.0)) for batch in stock_batches)
        if not stock_batches:
            status = "MISSING"
        elif available < required_quantity:
            status = "INSUFFICIENT"
        else:
            status = "OK"

        items.append(
            RecipeInventoryValidationItem(
                ingredient_type=ingredient_type,
                name=name,
                sku=sku,
                lookup_key=lookup_key,
                required_quantity=round(required_quantity, 4),
                unit=unit,
                available_quantity=round(available, 4),
                status=status,
                matched_batches=len(stock_batches),
            )
        )

    for fermentable in _copy_dict_list(recipe.fermentables):
        name = fermentable.get("name") or "FERMENTABLE"
        sku = fermentable.get("sku")
        required = float(fermentable.get("amount_kg", 0.0)) * scale_factor
        await _check_item("FERMENTABLE", name, sku, required, "KG")

    for hop in _copy_dict_list(recipe.hops):
        name = hop.get("name") or "HOP"
        sku = hop.get("sku")
        required_kg = (float(hop.get("amount_g", 0.0)) / 1000.0) * scale_factor
        await _check_item("HOP", name, sku, required_kg, "KG")

    for yeast in _copy_dict_list(recipe.yeast):
        name = yeast.get("name") or "YEAST"
        sku = yeast.get("sku")
        required_packets = float(yeast.get("amount_packets") or 1.0) * scale_factor
        await _check_item("YEAST", name, sku, required_packets, "PACKET")

    all_available = all(item.status == "OK" for item in items)
    return RecipeInventoryValidationResponse(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        scale_factor=round(scale_factor, 4),
        planned_volume_liters=planned_volume,
        items=items,
        all_available=all_available,
    )


@router.patch("/batches/{batch_id}/complete", response_model=BatchTransitionResponse)
async def complete_batch(
    batch_id: int,
    volume_update: UpdateBatchVolumeRequest,
    inventory_client: InventoryServiceClient = Depends(get_inventory_client),
    finance_client: FinanceServiceClient = Depends(get_finance_client),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    db: Session = Depends(get_db)
):
    """
    Mark batch COMPLETED and finalize costs.
    
    Sprint 4.5: Creates FinishedProductInventory and InternalTransfer (Factory → Taproom).
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    previous_status = batch.status
    
    # Update actual volume
    batch.actual_volume_liters = volume_update.actual_volume_liters
    batch.actual_og = volume_update.actual_og
    batch.actual_fg = volume_update.actual_fg
    
    # Recalculate cost per liter with actual volume
    if batch.total_cost:
        from decimal import Decimal as Dec
        batch.cost_per_liter = batch.total_cost / Dec(str(batch.actual_volume_liters))
    
    # Calculate ABV if we have OG and FG
    if batch.actual_og and batch.actual_fg:
        batch.actual_abv = (float(batch.actual_og) - float(batch.actual_fg)) * 131.25
    
    # Transition to COMPLETED
    try:
        BatchStateMachine.transition(batch, BatchStatus.COMPLETED)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # 1. Create FinishedProductInventory in Inventory Service
    finished_product = None
    internal_transfer = None
    
    try:
        finished_product = await inventory_client.create_finished_product(
            production_batch_id=batch.id,
            sku=batch.batch_number,
            product_name=batch.recipe_name,
            actual_volume_liters=float(batch.actual_volume_liters),
            unit_cost=float(batch.cost_per_liter),
            cold_room_id="COLD_ROOM_A",
            notes=f"Completed from batch {batch.batch_number}",
        )
    except httpx.HTTPError as e:
        db.rollback()
        raise HTTPException(503, f"Failed to create finished product: {str(e)}")
    
    # 2. Create InternalTransfer in Finance Service (Factory → Taproom)
    try:
        internal_transfer = await finance_client.create_internal_transfer(
            origin_type="house",  # Finance service expects lower-case
            quantity=float(batch.actual_volume_liters),
            unit_measure="LITERS",
            unit_cost=float(batch.cost_per_liter),
            product_sku=batch.recipe_name,
            product_name=batch.recipe_name,
            profit_center_from="factory",
            profit_center_to="taproom",
            notes=f"Batch {batch.batch_number} transfer",
            created_by_user_id=batch.created_by_user_id,
        )
    except httpx.HTTPError as e:
        db.rollback()
        raise HTTPException(503, f"Failed to create internal transfer: {str(e)}")
    
    db.commit()
    
    # 3. Publish batch_completed event
    try:
        event_publisher.publish(
            routing_key="production.batch_completed",
            message={
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "recipe_name": batch.recipe_name,
                "actual_volume_liters": float(batch.actual_volume_liters),
                "cost_per_liter": float(batch.cost_per_liter),
                "total_cost": float(batch.total_cost),
                "finished_product_id": finished_product['id'] if finished_product else None,
                "internal_transfer_id": internal_transfer['id'] if internal_transfer else None,
                "actual_abv": float(batch.actual_abv) if batch.actual_abv else None
            }
        )
    except Exception as e:
        print(f"Warning: Failed to publish batch_completed event: {e}")
    
    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.completed_at,
        message=(
            f"Batch completed. Volume: {batch.actual_volume_liters}L, Cost/L: ${batch.cost_per_liter}. "
            f"Created: FinishedProduct #{finished_product['id'] if finished_product else 'N/A'}, "
            f"InternalTransfer #{internal_transfer['id'] if internal_transfer else 'N/A'}"
        )
    )


# ===========================
# Cost Allocation Endpoints (2)
# ===========================

@router.get("/batches/{batch_id}/cost-breakdown", response_model=CostBreakdownResponse)
def get_cost_breakdown(batch_id: int, db: Session = Depends(get_db)):
    """Get detailed cost breakdown for batch."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    # Get allocations
    allocations = db.query(BatchIngredientAllocation).filter(
        BatchIngredientAllocation.production_batch_id == batch_id
    ).all()
    
    allocation_details = [
        {
            'ingredient': a.ingredient_name,
            'category': a.ingredient_category,
            'quantity': float(a.quantity_consumed),
            'unit': a.unit_measure,
            'unit_cost': float(a.unit_cost),
            'total_cost': float(a.total_cost),
            'stock_batch': a.stock_batch_number
        }
        for a in allocations
    ]
    
    return CostBreakdownResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        total_cost=float(batch.total_cost) if batch.total_cost else 0.0,
        cost_per_liter=float(batch.cost_per_liter) if batch.cost_per_liter else 0.0,
        breakdown={
            'malt': float(batch.malt_cost) if batch.malt_cost else 0.0,
            'hops': float(batch.hops_cost) if batch.hops_cost else 0.0,
            'yeast': float(batch.yeast_cost) if batch.yeast_cost else 0.0,
            'water': float(batch.water_cost) if batch.water_cost else 0.0,
            'labor': float(batch.labor_cost) if batch.labor_cost else 0.0,
            'overhead': float(batch.overhead_cost) if batch.overhead_cost else 0.0
        },
        allocations=allocation_details
    )
