"""
FastAPI routes for Sales Notes CRUD with PDF/PNG export.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from decimal import Decimal
import io

from database import get_db
from models.sales_note import SalesNote, SalesNoteItem
from models.client import Client
from schemas.sales_note import (
    SalesNoteCreate,
    SalesNoteUpdate,
    SalesNoteResponse,
    SalesNoteItemResponse,
)

router = APIRouter(prefix="/api/v1/sales/notes", tags=["Sales Notes"])


def _generate_note_number(db: Session) -> str:
    """Auto-generate 8-digit zero-padded note number."""
    last = db.query(SalesNote).order_by(SalesNote.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"{next_num:08d}"


def _build_note_response(note: SalesNote, items: list[SalesNoteItem]) -> dict:
    """Build response dict with items."""
    return {
        **{c.name: getattr(note, c.name) for c in note.__table__.columns},
        "items": [
            {c.name: getattr(item, c.name) for c in item.__table__.columns}
            for item in items
        ],
    }


@router.post("", response_model=SalesNoteResponse, status_code=201)
def create_sales_note(payload: SalesNoteCreate, db: Session = Depends(get_db)):
    """
    Create a new sales note with items.

    Totals are auto-calculated. Tax inclusion controlled by include_taxes flag.
    """
    # Resolve client name if client_id provided
    client_name = payload.client_name
    if payload.client_id:
        client = db.query(Client).filter(Client.id == payload.client_id).first()
        if client:
            client_name = client_name or client.business_name

    note = SalesNote(
        note_number=_generate_note_number(db),
        client_id=payload.client_id,
        client_name=client_name,
        channel=payload.channel,
        payment_method=payload.payment_method,
        include_taxes=payload.include_taxes,
        notes=payload.notes,
        created_by=payload.created_by,
    )
    db.add(note)
    db.flush()  # Get note.id

    # Create items
    items = []
    for item_data in payload.items:
        item = SalesNoteItem(
            sales_note_id=note.id,
            product_id=item_data.product_id,
            sku=item_data.sku,
            product_name=item_data.product_name,
            unit_measure=item_data.unit_measure,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount_pct=item_data.discount_pct,
            subtotal=0,
            line_total=0,
        )
        item.calculate_totals(
            include_taxes=payload.include_taxes,
            ieps_rate=item_data.ieps_rate,
            iva_rate=item_data.iva_rate,
        )
        db.add(item)
        items.append(item)

    # Recalculate note totals
    note.recalculate_totals(items)

    db.commit()
    db.refresh(note)

    # Reload items
    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note.id).all()
    return _build_note_response(note, items)


@router.get("", response_model=list[SalesNoteResponse])
def list_sales_notes(
    client_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None, description="DRAFT, CONFIRMED, CANCELLED"),
    channel: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List sales notes with filters."""
    query = db.query(SalesNote)

    if client_id:
        query = query.filter(SalesNote.client_id == client_id)
    if status:
        query = query.filter(SalesNote.status == status.upper())
    if channel:
        query = query.filter(SalesNote.channel == channel.upper())
    if payment_status:
        query = query.filter(SalesNote.payment_status == payment_status.upper())

    notes = query.order_by(SalesNote.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for note in notes:
        items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note.id).all()
        results.append(_build_note_response(note, items))
    return results


@router.get("/{note_id}", response_model=SalesNoteResponse)
def get_sales_note(note_id: int, db: Session = Depends(get_db)):
    """Get sales note with all items."""
    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")

    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()
    return _build_note_response(note, items)


@router.patch("/{note_id}", response_model=SalesNoteResponse)
def update_sales_note(note_id: int, payload: SalesNoteUpdate, db: Session = Depends(get_db)):
    """Update a DRAFT sales note."""
    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")
    if note.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT notes can be modified")

    update_data = payload.model_dump(exclude_unset=True)

    # If include_taxes changed, recalculate totals
    taxes_changed = "include_taxes" in update_data and update_data["include_taxes"] != note.include_taxes

    for key, value in update_data.items():
        setattr(note, key, value)

    if taxes_changed:
        items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()
        note.recalculate_totals(items)

    db.commit()
    db.refresh(note)

    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()
    return _build_note_response(note, items)


@router.patch("/{note_id}/confirm", response_model=SalesNoteResponse)
def confirm_sales_note(note_id: int, db: Session = Depends(get_db)):
    """
    Confirm a DRAFT note (makes it immutable).

    Side Effects (when ENABLE_INVENTORY_DEDUCTION=true):
    - Deducts finished product inventory for each item with product_id
    - Calls Inventory Service via HTTP (same pattern as Production Service)
    - Items without product_id (e.g., "Envío") are skipped
    - If Inventory Service is unreachable, note is still confirmed but
      inventory_deduction_status will show the errors
    """
    import os

    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")
    if note.status != "DRAFT":
        raise HTTPException(status_code=400, detail=f"Note is already {note.status}")

    note.status = "CONFIRMED"
    note.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(note)

    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()

    # Inventory deduction (async, best-effort)
    inventory_results = []
    if os.getenv("ENABLE_INVENTORY_DEDUCTION", "false").lower() == "true":
        try:
            import asyncio
            from clients.inventory_client import InventoryServiceClient

            client = InventoryServiceClient()
            inventory_results = asyncio.run(
                client.deduct_items_for_note(items, note.note_number)
            )
        except Exception as e:
            inventory_results = [{"status": f"Integration error: {str(e)}"}]

    response = _build_note_response(note, items)
    if inventory_results:
        response["inventory_deduction_status"] = inventory_results
    return response


@router.patch("/{note_id}/cancel", response_model=SalesNoteResponse)
def cancel_sales_note(note_id: int, db: Session = Depends(get_db)):
    """Cancel a sales note."""
    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")
    if note.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Note is already cancelled")

    note.status = "CANCELLED"
    note.cancelled_at = datetime.utcnow()
    db.commit()
    db.refresh(note)

    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()
    return _build_note_response(note, items)


@router.get("/{note_id}/export/pdf")
def export_note_pdf(note_id: int, db: Session = Depends(get_db)):
    """
    Export sales note as PDF.

    Returns a downloadable PDF matching the Desert Brew Co. note format.
    """
    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")

    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()

    try:
        from logic.note_renderer import NoteRenderer
        pdf_bytes = NoteRenderer.render_pdf(note, items)
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF renderer not available. Install: pip install reportlab")

    buffer = io.BytesIO(pdf_bytes)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=pedido_{note.note_number}.pdf"},
    )


@router.get("/{note_id}/export/png")
def export_note_png(note_id: int, dpi: int = Query(150, ge=72, le=300), db: Session = Depends(get_db)):
    """
    Export sales note as PNG image.

    Renders PDF first, then converts to PNG.
    """
    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")

    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()

    try:
        from logic.note_renderer import NoteRenderer
        png_bytes = NoteRenderer.render_png(note, items, dpi=dpi)
    except ImportError:
        raise HTTPException(status_code=500, detail="PNG renderer not available. Install: pip install reportlab Pillow")

    buffer = io.BytesIO(png_bytes)
    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=pedido_{note.note_number}.png"},
    )
