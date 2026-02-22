"""
FastAPI routes for Client CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models.client import Client
from schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientBalanceResponse,
)

router = APIRouter(prefix="/api/v1/sales/clients", tags=["Clients"])


def _generate_client_code(db: Session) -> str:
    """Auto-generate client code like CLI-001, CLI-002..."""
    last = db.query(Client).order_by(Client.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"CLI-{next_num:04d}"


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    """Create a new client."""
    client = Client(
        client_code=_generate_client_code(db),
        **payload.model_dump(exclude_unset=False),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientResponse])
def list_clients(
    client_type: Optional[str] = Query(None, description="Filter by type: B2B, B2C, DISTRIBUTOR"),
    pricing_tier: Optional[str] = Query(None, description="Filter by tier"),
    active_only: bool = Query(True, description="Show only active clients"),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List clients with optional filters."""
    query = db.query(Client)

    if active_only:
        query = query.filter(Client.is_active == True)
    if client_type:
        query = query.filter(Client.client_type == client_type.upper())
    if pricing_tier:
        query = query.filter(Client.pricing_tier == pricing_tier.upper())
    if search:
        query = query.filter(Client.business_name.ilike(f"%{search}%"))

    clients = query.order_by(Client.business_name.asc()).offset(offset).limit(limit).all()
    return clients


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Get client details."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    """Update client details."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(client, key, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=200)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Soft-delete a client (sets is_active=False)."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    client.is_active = False
    db.commit()
    return {"message": f"Client {client.client_code} deactivated", "client_id": client_id}


@router.get("/{client_id}/balance", response_model=ClientBalanceResponse)
def get_client_balance(client_id: int, db: Session = Depends(get_db)):
    """
    Get client credit balance and keg status.

    Implements the Double-Gate Credit Control check.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    can_order, reasons = client.can_place_order(order_amount=0, kegs_requested=0)

    return ClientBalanceResponse(
        client_id=client.id,
        client_code=client.client_code,
        business_name=client.business_name,
        credit_limit=float(client.credit_limit) if client.credit_limit else None,
        current_balance=float(client.current_balance),
        available_credit=float(client.available_credit),
        max_kegs=client.max_kegs,
        current_kegs=client.current_kegs,
        available_kegs=client.available_kegs,
        can_order=can_order,
        blocking_reasons=reasons,
    )
