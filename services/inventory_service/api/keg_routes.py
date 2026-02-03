"""
API routes for Keg Asset Management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database import get_db
from models.keg_asset import KegAsset
from models.keg_transition import KegTransition
from models.keg_transfer import KegTransfer
from models.keg_enums import KegState
from logic.keg_fsm import KegStateMachine, InvalidTransitionError, ValidationError
from schemas.keg import (
    KegAssetCreate,
    KegAssetUpdate,
    KegAssetResponse,
    KegAssetWithHistory,
    KegTransitionRequest,
    KegTransitionResponse,
    KegBulkScanRequest,
    KegBulkOperationResponse,
    KegFillBatchRequest,
    KegTransferRequest,
    KegTransferResponse,
    KegAtRiskResponse
)

router = APIRouter()


@router.post("/kegs", response_model=KegAssetResponse, status_code=201)
def create_keg(
    keg_data: KegAssetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new keg asset.
    
    - Creates keg with unique serial number
    - Initial state: EMPTY
    - Returns created keg
    """
    # Check for duplicate serial number
    existing = db.query(KegAsset).filter(
        KegAsset.serial_number == keg_data.serial_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Keg with serial number {keg_data.serial_number} already exists"
        )
    
    # Check for duplicate RFID if provided
    if keg_data.rfid_tag:
        existing_rfid = db.query(KegAsset).filter(
            KegAsset.rfid_tag == keg_data.rfid_tag
        ).first()
        if existing_rfid:
            raise HTTPException(
                status_code=400,
                detail=f"RFID tag {keg_data.rfid_tag} already in use"
            )
    
    # Create keg
    keg = KegAsset(
        id=uuid.uuid4(),
        serial_number=keg_data.serial_number,
        rfid_tag=keg_data.rfid_tag,
        size_liters=keg_data.size_liters,
        keg_type=keg_data.keg_type.value,
        ownership=keg_data.ownership.value,
        guest_brewery_id=keg_data.guest_brewery_id,
        current_location=keg_data.current_location,
        current_state=KegState.EMPTY.value
    )
    
    db.add(keg)
    
    # Create initial transition log
    transition = KegTransition(
        keg_id=keg.id,
        from_state=KegState.EMPTY.value,
        to_state=KegState.EMPTY.value,
        location=keg_data.current_location,
        notes="Initial registration"
    )
    db.add(transition)
    
    db.commit()
    db.refresh(keg)
    
    return keg


@router.get("/kegs", response_model=List[KegAssetResponse])
def list_kegs(
    state: Optional[str] = Query(None, description="Filter by state"),
    location: Optional[str] = Query(None, description="Filter by location"),
    client_id: Optional[int] = Query(None, description="Filter by client"),
    batch_id: Optional[int] = Query(None, description="Filter by batch"),
    size_liters: Optional[int] = Query(None, description="Filter by size"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List kegs with optional filters.
    
    Supports filtering by:
    - state
    - location
    - client_id
    - batch_id
    - size_liters
    - is_active
    """
    query = db.query(KegAsset)
    
    # Apply filters
    if state:
        query = query.filter(KegAsset.current_state == state)
    if location:
        query = query.filter(KegAsset.current_location.ilike(f"%{location}%"))
    if client_id is not None:
        query = query.filter(KegAsset.client_id == client_id)
    if batch_id is not None:
        query = query.filter(KegAsset.production_batch_id == batch_id)
    if size_liters is not None:
        query = query.filter(KegAsset.size_liters == size_liters)
    if is_active is not None:
        query = query.filter(KegAsset.is_active == is_active)
    
    # Pagination
    kegs = query.offset(skip).limit(limit).all()
    
    return kegs


@router.get("/kegs/{keg_id}", response_model=KegAssetWithHistory)
def get_keg(
    keg_id: str,
    db: Session = Depends(get_db)
):
    """
    Get keg details with transition history.
    
    Returns:
    - Keg asset details
    - Full transition history (most recent first)
    """
    try:
        keg_uuid = uuid.UUID(keg_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid keg ID format")
    
    keg = db.query(KegAsset).filter(KegAsset.id == keg_uuid).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    
    # Load transitions (already ordered by relationship)
    transitions = keg.transitions
    
    return {
        **keg.__dict__,
        "transitions": transitions
    }


@router.patch("/kegs/{keg_id}/transition", response_model=KegTransitionResponse)
def transition_keg(
    keg_id: str,
    transition_req: KegTransitionRequest,
    db: Session = Depends(get_db)
):
    """
    Transition keg to new state with FSM validation.
    
    - Validates transition is allowed by FSM
    - Validates business rules
    - Creates audit log
    - Updates keg state
    """
    try:
        keg_uuid = uuid.UUID(keg_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid keg ID format")
    
    keg = db.query(KegAsset).filter(KegAsset.id == keg_uuid).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    
    # Build context
    context = {
        "location": transition_req.location,
        "batch_id": transition_req.batch_id,
        "client_id": transition_req.client_id
    }
    
    # Validate transition
    try:
        KegStateMachine.validate_transition(keg, transition_req.new_state, context)
    except (InvalidTransitionError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Store previous state
    old_state = keg.current_state
    
    # Apply state changes
    KegStateMachine.apply_state_changes(keg, transition_req.new_state, context)
    
    # Create transition log
    transition = KegTransition(
        keg_id=keg.id,
        from_state=old_state,
        to_state=transition_req.new_state.value,
        location=transition_req.location,
        user_id=transition_req.user_id,
        reason=transition_req.reason,
        notes=transition_req.notes
    )
    
    db.add(transition)
    db.commit()
    db.refresh(transition)
    
    return transition


@router.post("/kegs/bulk-scan", response_model=KegBulkOperationResponse)
def bulk_scan_kegs(
    bulk_req: KegBulkScanRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk state transition via RFID scanning.
    
    - Scans multiple kegs by RFID
    - Transitions all to target state
    - Transactional (all or nothing)
    - Returns summary with failures
    """
    bulk_op_id = f"BULK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    success_count = 0
    failed_count = 0
    failed_tags = []
    errors = []
    
    try:
        # Find all kegs by RFID
        kegs = db.query(KegAsset).filter(
            KegAsset.rfid_tag.in_(bulk_req.rfid_tags)
        ).all()
        
        # Check if all tags were found
        found_tags = {keg.rfid_tag for keg in kegs}
        missing_tags = set(bulk_req.rfid_tags) - found_tags
        
        if missing_tags:
            failed_tags.extend(list(missing_tags))
            failed_count = len(missing_tags)
            errors.append(f"RFIDs not found: {', '.join(missing_tags)}")
        
        # Context for all
        context = {"location": bulk_req.location}
        
        # Validate all transitions first (fail fast)
        for keg in kegs:
            try:
                KegStateMachine.validate_transition(keg, bulk_req.new_state, context)
            except (InvalidTransitionError, ValidationError) as e:
                failed_tags.append(keg.rfid_tag)
                failed_count += 1
                errors.append(f"{keg.serial_number}: {str(e)}")
        
        # If any validation failed, rollback
        if failed_count > 0:
            db.rollback()
            return KegBulkOperationResponse(
                success_count=0,
                failed_count=failed_count,
                bulk_operation_id=bulk_op_id,
                failed_rfid_tags=failed_tags,
                errors=errors
            )
        
        # Apply all transitions
        for keg in kegs:
            old_state = keg.current_state
            
            # Apply state changes
            KegStateMachine.apply_state_changes(keg, bulk_req.new_state, context)
            
            # Create transition log
            transition = KegTransition(
                keg_id=keg.id,
                from_state=old_state,
                to_state=bulk_req.new_state.value,
                location=bulk_req.location,
                user_id=bulk_req.user_id,
                notes=bulk_req.notes,
                bulk_operation_id=bulk_op_id
            )
            db.add(transition)
            success_count += 1
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")
    
    return KegBulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        bulk_operation_id=bulk_op_id,
        failed_rfid_tags=failed_tags,
        errors=errors
    )


@router.post("/kegs/fill-batch", response_model=KegBulkOperationResponse)
def fill_batch(
    fill_req: KegFillBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Fill multiple kegs from a production batch.
    
    - Validates all kegs are CLEAN
    - Transitions to FULL
    - Links batch_id
    - Increments cycle count
    """
    bulk_op_id = f"FILL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    success_count = 0
    errors = []
    
    try:
        # Find all kegs
        kegs = db.query(KegAsset).filter(
            KegAsset.id.in_(fill_req.keg_ids)
        ).all()
        
        if len(kegs) != len(fill_req.keg_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more kegs not found"
            )
        
        # Validate all are CLEAN
        for keg in kegs:
            if keg.current_state != KegState.CLEAN.value:
                errors.append(
                    f"{keg.serial_number} is {keg.current_state}, must be CLEAN"
                )
        
        if errors:
            raise HTTPException(status_code=400, detail="; ".join(errors))
        
        # Fill all kegs
        context = {"batch_id": fill_req.batch_id}
        
        for keg in kegs:
            old_state = keg.current_state
            
            # Apply state changes
            KegStateMachine.apply_state_changes(keg, KegState.FULL, context)
            
            # Create transition
            transition = KegTransition(
                keg_id=keg.id,
                from_state=old_state,
                to_state=KegState.FULL.value,
                user_id=fill_req.filled_by,
                notes=fill_req.notes or f"Filled with batch {fill_req.batch_id}",
                bulk_operation_id=bulk_op_id
            )
            db.add(transition)
            success_count += 1
        
        db.commit()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    return KegBulkOperationResponse(
        success_count=success_count,
        failed_count=0,
        bulk_operation_id=bulk_op_id
    )


@router.post("/kegs/transfer", response_model=KegTransferResponse)
def transfer_content(
    transfer_req: KegTransferRequest,
    db: Session = Depends(get_db)
):
    """
    Transfer beer content from one keg to others.
    
    Example: Transfer 60L keg → 2×30L kegs
    
    - Validates source keg is FULL
    - Validates target kegs are CLEAN
    - Creates transfer record
    - Updates batch_id on targets
    """
    # Get source keg
    source = db.query(KegAsset).filter(
        KegAsset.id == transfer_req.source_keg_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source keg not found")
    
    if source.current_state != KegState.FULL.value:
        raise HTTPException(
            status_code=400,
            detail=f"Source keg must be FULL, is {source.current_state}"
        )
    
    # Get target kegs
    targets = db.query(KegAsset).filter(
        KegAsset.id.in_(transfer_req.target_keg_ids)
    ).all()
    
    if len(targets) != len(transfer_req.target_keg_ids):
        raise HTTPException(status_code=404, detail="One or more target kegs not found")
    
    # Validate all targets are CLEAN
    for target in targets:
        if target.current_state != KegState.CLEAN.value:
            raise HTTPException(
                status_code=400,
                detail=f"{target.serial_number} must be CLEAN, is {target.current_state}"
            )
    
    try:
        # Create transfer record
        transfer = KegTransfer(
            source_keg_id=source.id,
            source_batch_id=source.production_batch_id,
            target_keg_ids=[str(keg_id) for keg_id in transfer_req.target_keg_ids],
            volume_transferred_liters=transfer_req.volume_transferred_liters,
            transferred_by=transfer_req.transferred_by,
            notes=transfer_req.notes
        )
        db.add(transfer)
        
        # Empty source keg
        source.current_state = KegState.EMPTY.value
        source.production_batch_id = None
        
        # Fill target kegs
        batch_id = source.production_batch_id
        for target in targets:
            target.current_state = KegState.FULL.value
            target.production_batch_id = batch_id
            target.cycle_count += 1
            target.last_filled_at = datetime.utcnow()
        
        db.commit()
        db.refresh(transfer)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    return transfer


@router.get("/kegs/at-risk", response_model=List[KegAtRiskResponse])
def get_kegs_at_risk(
    days_threshold: int = Query(30, ge=1, description="Days threshold"),
    db: Session = Depends(get_db)
):
    """
    Get kegs that have been IN_CLIENT for more than threshold days.
    
    Used to identify kegs at risk of being lost.
    """
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    
    # Find kegs in IN_CLIENT state
    kegs_in_client = db.query(KegAsset).filter(
        KegAsset.current_state == KegState.IN_CLIENT.value,
        KegAsset.is_active == True
    ).all()
    
    at_risk = []
    
    for keg in kegs_in_client:
        # Get last transition to IN_CLIENT
        last_transition = db.query(KegTransition).filter(
            and_(
                KegTransition.keg_id == keg.id,
                KegTransition.to_state == KegState.IN_CLIENT.value
            )
        ).order_by(KegTransition.timestamp.desc()).first()
        
        if last_transition and last_transition.timestamp < cutoff_date:
            days_out = (datetime.now() - last_transition.timestamp).days
            
            at_risk.append(KegAtRiskResponse(
                keg_id=keg.id,
                serial_number=keg.serial_number,
                client_id=keg.client_id,
                client_name=None,  # Would come from client service
                days_out=days_out,
                last_transition_date=last_transition.timestamp,
                current_location=keg.current_location
            ))
    
    # Sort by days_out descending
    at_risk.sort(key=lambda x: x.days_out, reverse=True)
    
    return at_risk


@router.patch("/kegs/{keg_id}", response_model=KegAssetResponse)
def update_keg(
    keg_id: str,
    keg_update: KegAssetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update keg attributes (not state).
    
    Use /kegs/{id}/transition for state changes.
    """
    try:
        keg_uuid = uuid.UUID(keg_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid keg ID format")
    
    keg = db.query(KegAsset).filter(KegAsset.id == keg_uuid).first()
    if not keg:
        raise HTTPException(status_code=404, detail="Keg not found")
    
    # Apply updates
    if keg_update.rfid_tag is not None:
        # Check for duplicate
        existing = db.query(KegAsset).filter(
            and_(
                KegAsset.rfid_tag == keg_update.rfid_tag,
                KegAsset.id != keg.id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"RFID tag already in use by {existing.serial_number}"
            )
        keg.rfid_tag = keg_update.rfid_tag
    
    if keg_update.current_location is not None:
        keg.current_location = keg_update.current_location
    
    if keg_update.needs_maintenance is not None:
        keg.needs_maintenance = keg_update.needs_maintenance
    
    keg.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(keg)
    
    return keg
