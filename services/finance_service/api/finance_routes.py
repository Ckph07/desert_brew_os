"""
FastAPI routes for Transfer Pricing and Internal Transfers.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models.transfer_pricing_rule import TransferPricingRule
from models.internal_transfer import InternalTransfer, ProfitCenter
from schemas.finance import (
    TransferPricingRuleResponse,
    InternalTransferRequest,
    InternalTransferResponse,
    ProfitCenterSummary,
    TransferPriceCalculation
)
from logic.transfer_pricing_engine import TransferPricingEngine

router = APIRouter(prefix="/api/v1/finance", tags=["Finance"])


@router.get("/pricing-rules", response_model=List[TransferPricingRuleResponse])
def get_pricing_rules(
    active_only: bool = Query(True, description="Show only active rules"),
    db: Session = Depends(get_db)
):
    """Get all transfer pricing rules."""
    query = db.query(TransferPricingRule)
    
    if active_only:
        query = query.filter_by(is_active=True)
    
    rules = query.all()
    return rules


@router.post("/calculate-transfer-price", response_model=TransferPriceCalculation)
def calculate_transfer_price(
    origin_type: str = Query(..., description="Product origin"),
    unit_cost: float = Query(..., gt=0, description="Factory unit cost"),
    db: Session = Depends(get_db)
):
    """
    Calculate transfer price for given origin and cost.
    
    Does NOT create a transfer record, just returns pricing calculation.
    """
    try:
        unit_transfer_price, rule = TransferPricingEngine.get_transfer_price(
            origin_type=origin_type,
            unit_cost=unit_cost,
            db=db
        )
        
        return TransferPriceCalculation(
            origin_type=origin_type,
            unit_cost=unit_cost,
            unit_transfer_price=unit_transfer_price,
            markup_percentage=float(rule.markup_percentage),
            strategy=rule.strategy,
            rule_name=rule.rule_name
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/internal-transfers", response_model=InternalTransferResponse, status_code=201)
def create_internal_transfer(
    transfer: InternalTransferRequest,
    db: Session = Depends(get_db)
):
    """
    Create internal transfer from Factory to Taproom.
    
    Automatically calculates transfer pricing based on origin type.
    Records in Shadow Ledger for P&L segregation.
    """
    # Calculate transfer pricing
    try:
        pricing = TransferPricingEngine.calculate_batch_transfer(
            origin_type=transfer.origin_type,
            quantity=transfer.quantity,
            unit_cost=transfer.unit_cost,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create transfer record
    internal_transfer = InternalTransfer(
        from_profit_center=transfer.from_profit_center,
        to_profit_center=transfer.to_profit_center,
        product_sku=transfer.product_sku,
        product_name=transfer.product_name,
        origin_type=transfer.origin_type,
        quantity=transfer.quantity,
        unit_measure=transfer.unit_measure,
        unit_cost=pricing['unit_cost'],
        unit_transfer_price=pricing['unit_transfer_price'],
        total_cost=pricing['total_cost'],
        total_transfer_price=pricing['total_transfer_price'],
        factory_revenue=pricing['factory_revenue'],
        factory_profit=pricing['factory_profit'],
        taproom_cogs=pricing['taproom_cogs'],
        pricing_rule_id=pricing['pricing_rule_id'],
        markup_percentage=pricing['markup_percentage'],
        notes=transfer.notes,
        created_by_user_id=transfer.created_by_user_id
    )
    
    db.add(internal_transfer)
    db.commit()
    db.refresh(internal_transfer)
    
    return InternalTransferResponse(
        id=str(internal_transfer.id),
        from_profit_center=internal_transfer.from_profit_center,
        to_profit_center=internal_transfer.to_profit_center,
        product_sku=internal_transfer.product_sku,
        quantity=float(internal_transfer.quantity),
        unit_cost=float(internal_transfer.unit_cost),
        unit_transfer_price=float(internal_transfer.unit_transfer_price),
        total_cost=float(internal_transfer.total_cost),
        total_transfer_price=float(internal_transfer.total_transfer_price),
        factory_revenue=float(internal_transfer.factory_revenue),
        factory_profit=float(internal_transfer.factory_profit),
        taproom_cogs=float(internal_transfer.taproom_cogs),
        markup_percentage=float(internal_transfer.markup_percentage),
        transfer_date=internal_transfer.transfer_date
    )


@router.get("/internal-transfers", response_model=List[InternalTransferResponse])
def list_internal_transfers(
    profit_center: str = Query(None, description="Filter by profit center"),
    origin_type: str = Query(None, description="Filter by origin type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List internal transfers with filters."""
    query = db.query(InternalTransfer)
    
    if profit_center:
        query = query.filter(
            (InternalTransfer.from_profit_center == profit_center) |
            (InternalTransfer.to_profit_center == profit_center)
        )
    
    if origin_type:
        query = query.filter(InternalTransfer.origin_type == origin_type)
    
    transfers = query.order_by(InternalTransfer.transfer_date.desc()).offset(skip).limit(limit).all()
    
    return [
        InternalTransferResponse(
            id=str(t.id),
            from_profit_center=t.from_profit_center,
            to_profit_center=t.to_profit_center,
            product_sku=t.product_sku,
            quantity=float(t.quantity),
            unit_cost=float(t.unit_cost),
            unit_transfer_price=float(t.unit_transfer_price),
            total_cost=float(t.total_cost),
            total_transfer_price=float(t.total_transfer_price),
            factory_revenue=float(t.factory_revenue),
            factory_profit=float(t.factory_profit),
            taproom_cogs=float(t.taproom_cogs),
            markup_percentage=float(t.markup_percentage),
            transfer_date=t.transfer_date
        )
        for t in transfers
    ]


@router.get("/profit-center/{profit_center}/summary", response_model=ProfitCenterSummary)
def get_profit_center_summary(
    profit_center: str,
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get P&L summary for a profit center.
    
    For Factory: revenue = factory_revenue, cogs = total_cost
    For Taproom: revenue = (from actual sales - future), cogs = taproom_cogs
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()
    
    if profit_center.lower() == "factory":
        # Factory perspective
        transfers = db.query(InternalTransfer).filter(
            InternalTransfer.from_profit_center == ProfitCenter.FACTORY.value,
            InternalTransfer.transfer_date >= period_start
        ).all()
        
        total_revenue = sum(float(t.factory_revenue) for t in transfers)
        total_cogs = sum(float(t.total_cost) for t in transfers)
        
    elif profit_center.lower() == "taproom":
        # Taproom perspective
        transfers = db.query(InternalTransfer).filter(
            InternalTransfer.to_profit_center == ProfitCenter.TAPROOM.value,
            InternalTransfer.transfer_date >= period_start
        ).all()
        
        # Taproom's "COGS" is the transfer price from Factory
        total_cogs = sum(float(t.taproom_cogs) for t in transfers)
        # TODO: Taproom revenue from actual sales (Sprint 7)
        total_revenue = 0.0  # Will be from POS in Sprint 7
        
    else:
        raise HTTPException(400, f"Unknown profit center: {profit_center}")
    
    total_profit = total_revenue - total_cogs
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
    
    return ProfitCenterSummary(
        profit_center=profit_center,
        period_start=period_start,
        period_end=period_end,
        total_revenue=round(total_revenue, 2),
        total_cogs=round(total_cogs, 2),
        total_profit=round(total_profit, 2),
        profit_margin_percentage=round(profit_margin, 2),
        transfer_count=len(transfers)
    )
