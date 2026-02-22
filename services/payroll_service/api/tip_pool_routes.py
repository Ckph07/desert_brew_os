"""
FastAPI routes for TipPool weekly distribution.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.employee import Employee, TipPool
from schemas.payroll import (
    TipPoolCreate,
    TipPoolResponse,
    TipPoolDetailResponse,
)

router = APIRouter(prefix="/api/v1/payroll", tags=["Tip Pools"])


@router.post("/tip-pools", response_model=TipPoolDetailResponse, status_code=201)
def create_tip_pool(payload: TipPoolCreate, db: Session = Depends(get_db)):
    """
    Create a weekly tip pool distribution (Sun-Sat).

    Divides total_collected equally among all participant_ids.
    Validates that all participants are eligible for tips.
    """
    # Validate participants
    participants = db.query(Employee).filter(
        Employee.id.in_(payload.participant_ids),
        Employee.is_active == True,
    ).all()

    if len(participants) != len(payload.participant_ids):
        found_ids = {p.id for p in participants}
        missing = set(payload.participant_ids) - found_ids
        raise HTTPException(status_code=404, detail=f"Employees not found: {missing}")

    # Check all are tip-eligible
    non_eligible = [p for p in participants if not p.eligible_for_tips]
    if non_eligible:
        names = [p.full_name for p in non_eligible]
        raise HTTPException(status_code=400, detail=f"Not eligible for tips: {names}")

    num = len(participants)
    per_person = round(payload.total_collected / num, 2)

    pool = TipPool(
        week_start=payload.week_start,
        week_end=payload.week_end,
        total_collected=payload.total_collected,
        num_participants=num,
        per_person_share=per_person,
        notes=payload.notes,
        created_by=payload.created_by,
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)

    participant_list = [
        {"employee_id": p.id, "name": p.full_name, "share": per_person}
        for p in participants
    ]

    return TipPoolDetailResponse(
        id=pool.id,
        week_start=pool.week_start,
        week_end=pool.week_end,
        total_collected=float(pool.total_collected),
        num_participants=pool.num_participants,
        per_person_share=float(pool.per_person_share),
        notes=pool.notes,
        created_by=pool.created_by,
        created_at=pool.created_at,
        participants=participant_list,
    )


@router.get("/tip-pools", response_model=list[TipPoolResponse])
def list_tip_pools(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List tip pool distributions (most recent first)."""
    return db.query(TipPool).order_by(TipPool.week_start.desc()).limit(limit).all()


@router.get("/tip-pools/{pool_id}", response_model=TipPoolResponse)
def get_tip_pool(pool_id: int, db: Session = Depends(get_db)):
    """Get tip pool details."""
    pool = db.query(TipPool).filter(TipPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail=f"TipPool {pool_id} not found")
    return pool
