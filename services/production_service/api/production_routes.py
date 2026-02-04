"""
Production Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
import tempfile
import os

from database import get_db
from models.recipe import Recipe
from models.production_batch import ProductionBatch, BatchStatus
from models.batch_ingredient_allocation import BatchIngredientAllocation
from schemas.production import (
    RecipeResponse,
    CreateBatchRequest,
    BatchResponse,
    BatchDetailResponse,
    UpdateBatchVolumeRequest,
    CostBreakdownResponse,
    BatchTransitionResponse
)
from logic.beersmith_parser import BeerSmithParser
from logic.batch_state_machine import BatchStateMachine
from logic.cost_allocator import CostAllocator

router = APIRouter(prefix="/api/v1/production", tags=["Production"])


# =====================
# Recipe Endpoints (4)
# =====================

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


# ===========================
# Production Batch Endpoints (6)
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
def start_brewing(batch_id: int, db: Session = Depends(get_db)):
    """Transition batch: PLANNED → BREWING and allocate costs."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    previous_status = batch.status
    
    # Transition state
    try:
        BatchStateMachine.transition(batch, BatchStatus.BREWING, notes="Started brewing")
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # Allocate costs via FIFO
    recipe = db.query(Recipe).filter(Recipe.id == batch.recipe_id).first()
    CostAllocator.allocate_batch_costs(batch, recipe, db)
    
    db.commit()
    
    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.brewing_started_at,
        message=f"Batch started brewing. Total cost allocated: ${batch.total_cost}"
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


@router.patch("/batches/{batch_id}/complete", response_model=BatchTransitionResponse)
def complete_batch(
    batch_id: int,
    volume_update: UpdateBatchVolumeRequest,
    db: Session = Depends(get_db)
):
    """
    Mark batch COMPLETED and finalize costs.
    
    Future: Create FinishedProductInventory and InternalTransfer (Sprint 4.5).
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    previous_status = batch.status
    
    # Update actual volume
    batch.actual_volume_liters = volume_update.actual_volume_liters
    batch.actual_og = volume_update.actual_og
    batch.actual_fg = volume_update.actual_fg
    
    # Recalculate cost per liter
    if batch.total_cost:
        batch.cost_per_liter = batch.total_cost / batch.actual_volume_liters
    
    # Calculate ABV if we have OG and FG
    if batch.actual_og and batch.actual_fg:
        batch.actual_abv = (float(batch.actual_og) - float(batch.actual_fg)) * 131.25
    
    # Transition to COMPLETED
    try:
        BatchStateMachine.transition(batch, BatchStatus.COMPLETED)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    db.commit()
    
    # TODO Sprint 4.5: Create FinishedProductInventory
    # TODO Sprint 4.5: Create InternalTransfer to Taproom
    
    return BatchTransitionResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        previous_status=previous_status,
        new_status=batch.status,
        timestamp=batch.completed_at,
        message=f"Batch completed. Actual volume: {batch.actual_volume_liters}L, Cost/L: ${batch.cost_per_liter}"
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
