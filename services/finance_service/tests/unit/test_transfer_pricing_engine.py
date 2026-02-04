"""
Unit tests for Transfer Pricing Engine.
"""
import pytest
from logic.transfer_pricing_engine import TransferPricingEngine


class TestTransferPricingEngine:
    """Test transfer pricing calculations."""
    
    def test_get_transfer_price_house(self, db_session, seeded_pricing_rules):
        """Test HOUSE beer pricing (15% markup)."""
        unit_cost = 500.00  # Factory cost
        
        transfer_price, rule = TransferPricingEngine.get_transfer_price(
            origin_type="house",
            unit_cost=unit_cost,
            db=db_session
        )
        
        # 500 × 1.15 = 575.00
        assert transfer_price == 575.00
        assert rule.origin_type == "house"
        assert float(rule.markup_percentage) == 15.00
    
    def test_get_transfer_price_guest(self, db_session, seeded_pricing_rules):
        """Test GUEST beer pricing (0% markup - passthrough)."""
        unit_cost = 300.00
        
        transfer_price, rule = TransferPricingEngine.get_transfer_price(
            origin_type="guest",
            unit_cost=unit_cost,
            db=db_session
        )
        
        # 300 × 1.00 = 300.00 (passthrough)
        assert transfer_price == 300.00
        assert float(rule.markup_percentage) == 0.00
    
    def test_get_transfer_price_merchandise(self, db_session, seeded_pricing_rules):
        """Test MERCHANDISE pricing (25% markup)."""
        unit_cost = 100.00
        
        transfer_price, rule = TransferPricingEngine.get_transfer_price(
            origin_type="merchandise",
            unit_cost=unit_cost,
            db=db_session
        )
        
        # 100 × 1.25 = 125.00
        assert transfer_price == 125.00
        assert float(rule.markup_percentage) == 25.00
    
    def test_get_transfer_price_no_rule(self, db_session):
        """Test error when no pricing rule exists."""
        with pytest.raises(ValueError) as exc:
            TransferPricingEngine.get_transfer_price(
                origin_type="unknown",
                unit_cost=100.00,
                db=db_session
            )
        
        assert "No active pricing rule" in str(exc.value)
    
    def test_calculate_batch_transfer(self, db_session, seeded_pricing_rules):
        """Test full batch transfer calculation."""
        result = TransferPricingEngine.calculate_batch_transfer(
            origin_type="house",
            quantity=10.0,  # 10 kegs
            unit_cost=500.00,  # $500/keg
            db=db_session
        )
        
        assert result['unit_cost'] == 500.00
        assert result['unit_transfer_price'] == 575.00  # 500 × 1.15
        assert result['total_cost'] == 5000.00  # 10 × 500
        assert result['total_transfer_price'] == 5750.00  # 10 × 575
        assert result['factory_revenue'] == 5750.00
        assert result['factory_profit'] == 750.00  # 5750 - 5000
        assert result['taproom_cogs'] == 5750.00
        assert result['markup_percentage'] == 15.00
    
    def test_calculate_batch_transfer_passthrough(self, db_session, seeded_pricing_rules):
        """Test guest beer (no factory profit)."""
        result = TransferPricingEngine.calculate_batch_transfer(
            origin_type="guest",
            quantity=5.0,
            unit_cost=300.00,
            db=db_session
        )
        
        assert result['total_cost'] == 1500.00  # 5 × 300
        assert result['total_transfer_price'] == 1500.00  # Same (passthrough)
        assert result['factory_profit'] == 0.00  # No profit
    
    def test_validate_pricing_rules(self, db_session, seeded_pricing_rules):
        """Test validation of complete rule set."""
        missing = TransferPricingEngine.validate_pricing_rules(db_session)
        
        assert len(missing) == 0  # All origins covered
    
    def test_validate_pricing_rules_incomplete(self, db_session):
        """Test detection of missing rules."""
        from models.transfer_pricing_rule import TransferPricingRule
        
        # Only add one rule
        rule = TransferPricingRule(
            origin_type="house",
            strategy="cost_plus",
            markup_percentage=15.00,
            rule_name="Test",
            is_active=True
        )
        db_session.add(rule)
        db_session.commit()
        
        missing = TransferPricingEngine.validate_pricing_rules(db_session)
        
        assert 'guest' in missing
        assert 'commercial' in missing
        assert 'merchandise' in missing
