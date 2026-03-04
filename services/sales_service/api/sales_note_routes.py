"""
FastAPI routes for Sales Notes CRUD with PDF/PNG export.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from datetime import datetime, date
import io

from database import get_db
from models.sales_note import SalesNote, SalesNoteItem
from models.client import Client
from models.product_catalog import ProductCatalog
from schemas.sales_note import (
    SalesNoteCreate,
    SalesNoteUpdate,
    SalesNotePaymentUpdate,
    SalesNoteResponse,
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


def _resolve_tax_toggles(
    *,
    include_taxes: bool,
    include_ieps: Optional[bool],
    include_iva: Optional[bool],
) -> tuple[bool, bool, bool]:
    """Resolve legacy + new tax toggle payload fields."""
    ieps_enabled = include_ieps if include_ieps is not None else include_taxes
    iva_enabled = include_iva if include_iva is not None else include_taxes
    taxes_enabled = bool(ieps_enabled or iva_enabled)
    return taxes_enabled, bool(ieps_enabled), bool(iva_enabled)


def _is_beer_item(item_data, product: Optional[ProductCatalog]) -> bool:
    """Determine if IEPS can apply to this line item."""
    if product and product.category:
        return product.category.upper().startswith("BEER")

    sku = (item_data.sku or "").upper()
    if sku.startswith("BEER"):
        return True

    name = (item_data.product_name or "").upper()
    beer_keywords = (
        "CERVEZA",
        "IPA",
        "LAGER",
        "STOUT",
        "ALE",
        "PORTER",
        "PILS",
        "HEFE",
        "TRIGO",
    )
    return any(keyword in name for keyword in beer_keywords)


def _resolve_item_tax_rates(
    *,
    item_data,
    product: Optional[ProductCatalog],
    include_ieps: bool,
    include_iva: bool,
) -> tuple[float, float]:
    """Resolve final tax rates for an item according to business rules."""
    is_beer = _is_beer_item(item_data, product)

    raw_ieps = item_data.ieps_rate
    if raw_ieps is None and product and product.ieps_rate is not None:
        raw_ieps = float(product.ieps_rate)
    ieps_rate = float(raw_ieps or 0)
    if not include_ieps or not is_beer:
        ieps_rate = 0.0

    raw_iva = item_data.iva_rate
    if raw_iva is None and product and product.iva_rate is not None:
        raw_iva = float(product.iva_rate)
    iva_rate = float(raw_iva if raw_iva is not None else 0.16)
    if not include_iva:
        iva_rate = 0.0

    return ieps_rate, iva_rate


@router.post("", response_model=SalesNoteResponse, status_code=201)
def create_sales_note(payload: SalesNoteCreate, db: Session = Depends(get_db)):
    """
    Create a new sales note with items.

    Totals are auto-calculated.
    Tax toggles can be controlled independently (`include_ieps`, `include_iva`).
    """
    # Resolve client name if client_id provided
    client_name = payload.client_name
    if payload.client_id:
        client = db.query(Client).filter(Client.id == payload.client_id).first()
        if client:
            client_name = client_name or client.business_name

    include_taxes, include_ieps, include_iva = _resolve_tax_toggles(
        include_taxes=payload.include_taxes,
        include_ieps=payload.include_ieps,
        include_iva=payload.include_iva,
    )

    product_ids = [item.product_id for item in payload.items if item.product_id]
    products_by_id: dict[int, ProductCatalog] = {}
    if product_ids:
        products = db.query(ProductCatalog).filter(ProductCatalog.id.in_(product_ids)).all()
        products_by_id = {int(product.id): product for product in products}

    note = SalesNote(
        note_number=_generate_note_number(db),
        client_id=payload.client_id,
        client_name=client_name,
        channel=payload.channel,
        payment_method=payload.payment_method,
        include_taxes=include_taxes,
        include_ieps=include_ieps,
        include_iva=include_iva,
        notes=payload.notes,
        created_by=payload.created_by,
    )
    db.add(note)
    db.flush()  # Get note.id

    # Create items
    items = []
    for item_data in payload.items:
        product = products_by_id.get(item_data.product_id) if item_data.product_id else None
        ieps_rate, iva_rate = _resolve_item_tax_rates(
            item_data=item_data,
            product=product,
            include_ieps=include_ieps,
            include_iva=include_iva,
        )
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
            include_ieps=include_ieps,
            include_iva=include_iva,
            ieps_rate=ieps_rate,
            iva_rate=iva_rate,
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

    current_ieps = bool(getattr(note, "include_ieps", note.include_taxes))
    current_iva = bool(getattr(note, "include_iva", note.include_taxes))

    if "include_taxes" in update_data:
        if "include_ieps" not in update_data:
            update_data["include_ieps"] = bool(update_data["include_taxes"])
        if "include_iva" not in update_data:
            update_data["include_iva"] = bool(update_data["include_taxes"])

    if "include_ieps" in update_data or "include_iva" in update_data:
        ieps_enabled = bool(update_data.get("include_ieps", current_ieps))
        iva_enabled = bool(update_data.get("include_iva", current_iva))
        update_data["include_taxes"] = bool(ieps_enabled or iva_enabled)

    taxes_changed = (
        ("include_taxes" in update_data and update_data["include_taxes"] != note.include_taxes)
        or ("include_ieps" in update_data and update_data["include_ieps"] != current_ieps)
        or ("include_iva" in update_data and update_data["include_iva"] != current_iva)
    )

    for key, value in update_data.items():
        setattr(note, key, value)

    if taxes_changed:
        items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()
        note.recalculate_totals(items)

    db.commit()
    db.refresh(note)

    items = db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).all()
    return _build_note_response(note, items)


@router.delete("/{note_id}", status_code=204)
def delete_sales_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a DRAFT sales note and its items."""
    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")
    if note.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only DRAFT notes can be deleted")

    db.query(SalesNoteItem).filter(SalesNoteItem.sales_note_id == note_id).delete()
    db.delete(note)
    db.commit()
    return Response(status_code=204)


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
                client.deduct_items_for_note(
                    items,
                    note.note_number,
                    user_id=note.created_by,
                )
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


@router.patch("/{note_id}/payment", response_model=SalesNoteResponse)
def update_sales_note_payment(
    note_id: int,
    payload: SalesNotePaymentUpdate,
    db: Session = Depends(get_db),
):
    """Update payment status for a CONFIRMED sales note."""
    note = db.query(SalesNote).filter(SalesNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Sales note {note_id} not found")

    if note.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot update payment on CANCELLED note")
    if note.status != "CONFIRMED":
        raise HTTPException(status_code=400, detail="Only CONFIRMED notes can update payment status")

    new_status = payload.payment_status.upper()
    allowed = {"PAID", "PENDING", "PARTIAL", "OVERDUE"}
    if new_status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid payment_status '{payload.payment_status}'. Allowed: {sorted(allowed)}",
        )

    note.payment_status = new_status
    note.paid_at = datetime.utcnow() if new_status == "PAID" else None
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

# ── Liters by Style Analytics ───────────────────────────────────────────────────────

@router.get("/analytics/liters-by-style")
def liters_by_style(
    since: Optional[date] = Query(None, description="Start date (inclusive), YYYY-MM-DD"),
    until: Optional[date] = Query(None, description="End date (inclusive), YYYY-MM-DD"),
    channel: Optional[str] = Query(None, description="Filter by channel: B2B, TAPROOM, DISTRIBUTOR ..."),
    db: Session = Depends(get_db),
):
    """
    Liters sold aggregated by beer style — CONFIRMED notes only.

    Joins SalesNoteItem → ProductCatalog to resolve `style`.
    Items without a product_id (e.g. shipping) use the product_name as fallback style label.
    Only items with unit_measure IN ('LITROS', 'L') are counted.

    Returns a list ordered by total_liters DESC:
    [
      {"style": "Imperial IPA", "total_liters": 432.0, "note_count": 18, "revenue": 47289.60},
      ...
    ]
    """
    liter_units = ("LITROS", "L")

    # Base sub-query: confirmed note IDs
    confirmed_note_ids = (
        db.query(SalesNote.id)
        .filter(SalesNote.status == "CONFIRMED")
    )
    if since:
        confirmed_note_ids = confirmed_note_ids.filter(
            func.date(SalesNote.confirmed_at) >= since
        )
    if until:
        confirmed_note_ids = confirmed_note_ids.filter(
            func.date(SalesNote.confirmed_at) <= until
        )
    if channel:
        confirmed_note_ids = confirmed_note_ids.filter(
            SalesNote.channel == channel.upper()
        )
    confirmed_ids = [r.id for r in confirmed_note_ids.all()]

    if not confirmed_ids:
        return {
            "since": str(since) if since else None,
            "until": str(until) if until else None,
            "total_liters": 0.0,
            "styles": [],
        }

    # Aggregate: JOIN items → product_catalog, group by style
    style_expr = func.coalesce(
        ProductCatalog.style, SalesNoteItem.product_name
    ).label("style")

    rows = (
        db.query(
            style_expr,
            func.sum(
                case(
                    (
                        func.upper(SalesNoteItem.unit_measure).in_(liter_units),
                        SalesNoteItem.quantity,
                    ),
                    else_=0,
                )
            ).label("total_liters"),
            func.count(func.distinct(SalesNoteItem.sales_note_id)).label("note_count"),
            func.sum(
                case(
                    (
                        func.upper(SalesNoteItem.unit_measure).in_(liter_units),
                        SalesNoteItem.line_total,
                    ),
                    else_=0,
                )
            ).label("revenue"),
        )
        .outerjoin(
            ProductCatalog,
            SalesNoteItem.product_id == ProductCatalog.id,
        )
        .filter(
            SalesNoteItem.sales_note_id.in_(confirmed_ids),
            func.upper(SalesNoteItem.unit_measure).in_(liter_units),
        )
        .group_by(style_expr)
        .order_by(func.sum(
            case(
                (
                    func.upper(SalesNoteItem.unit_measure).in_(liter_units),
                    SalesNoteItem.quantity,
                ),
                else_=0,
            )
        ).desc())
        .all()
    )

    styles = [
        {
            "style": row.style or "Sin estilo",
            "total_liters": float(row.total_liters or 0),
            "note_count": row.note_count,
            "revenue": float(row.revenue or 0),
        }
        for row in rows
    ]

    grand_total = sum(s["total_liters"] for s in styles)
    # Add percentage share per style
    for s in styles:
        s["pct"] = round(s["total_liters"] / grand_total * 100, 1) if grand_total else 0.0

    return {
        "since": str(since) if since else None,
        "until": str(until) if until else None,
        "channel": channel,
        "total_liters": grand_total,
        "styles": styles,
    }
