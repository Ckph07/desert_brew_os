"""
Transfer Pricing Engine - Calculate transfer prices by origin type.

Purpose: Apply pricing rules automatically when products move from Factory to Taproom.
"""
from sqlalchemy.orm import Session
from models.transfer_pricing_rule import TransferPricingRule
from typing import Optional, Tuple


class TransferPricingEngine:
    """
    Engine for calculating transfer prices.
    
    Business Logic:
    - HOUSE beer: Factory earns 15% margin (COST_PLUS)
    - GUEST beer: Factory earns 0% margin (PASSTHROUGH)
    - COMMERCIAL: Factory earns 0% margin (PASSTHROUGH)
    - MERCHANDISE: Configurable
    """
    
    @staticmethod
    def get_transfer_price(
        origin_type: str,
        unit_cost: float,
        db: Session
    ) -> Tuple[float, Optional[TransferPricingRule]]:
        """
        Calculate transfer price for given origin and cost.
        
        Args:
            origin_type: Product origin (HOUSE, GUEST, etc.)
            unit_cost: Factory's unit cost
            db: Database session
            
        Returns:
            (transfer_price, pricing_rule)
            
        Raises:
            ValueError: If no pricing rule found for origin
        """
        # Find active pricing rule
        rule = db.query(TransferPricingRule).filter_by(
            origin_type=origin_type,
            is_active=True
        ).first()
        
        if not rule:
            raise ValueError(f"No active pricing rule found for origin_type: {origin_type}")
        
        # Calculate transfer price
        transfer_price = rule.calculate_transfer_price(unit_cost)
        
        return (transfer_price, rule)
    
    @staticmethod
    def calculate_batch_transfer(
        origin_type: str,
        quantity: float,
        unit_cost: float,
        db: Session
    ) -> dict:
        """
        Calculate full transfer details for a batch.
        
        Returns:
            {
                'unit_cost': float,
                'unit_transfer_price': float,
                'total_cost': float,
                'total_transfer_price': float,
                'factory_revenue': float,
                'factory_profit': float,
                'taproom_cogs': float,
                'markup_percentage': float,
                'pricing_rule_id': int
            }
        """
        unit_transfer_price, rule = TransferPricingEngine.get_transfer_price(
            origin_type, unit_cost, db
        )
        
        total_cost = round(quantity * unit_cost, 2)
        total_transfer_price = round(quantity * unit_transfer_price, 2)
        
        factory_revenue = total_transfer_price
        factory_profit = round(total_transfer_price - total_cost, 2)
        taproom_cogs = total_transfer_price
        
        return {
            'unit_cost': round(unit_cost, 2),
            'unit_transfer_price': unit_transfer_price,
            'total_cost': total_cost,
            'total_transfer_price': total_transfer_price,
            'factory_revenue': factory_revenue,
            'factory_profit': factory_profit,
            'taproom_cogs': taproom_cogs,
            'markup_percentage': float(rule.markup_percentage),
            'pricing_rule_id': rule.id
        }
    
    @staticmethod
    def validate_pricing_rules(db: Session) -> list:
        """
        Validate that all origin types have pricing rules.
        
        Returns:
            List of missing origin types
        """
        expected_origins = ['house', 'guest', 'commercial', 'merchandise']
        
        existing_rules = db.query(TransferPricingRule).filter(
            TransferPricingRule.is_active == True
        ).all()
        
        existing_origins = {rule.origin_type for rule in existing_rules}
        missing_origins = set(expected_origins) - existing_origins
        
        return list(missing_origins)
