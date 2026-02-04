"""
Unit tests for InternalTransfer model.
"""
import pytest
from models.internal_transfer import InternalTransfer, ProfitCenter


class TestInternalTransferModel:
    """Test InternalTransfer model."""
    
    def test_create_internal_transfer(self, db_session):
        """Test creating an internal transfer."""
        transfer = InternalTransfer(
            from_profit_center=ProfitCenter.FACTORY.value,
            to_profit_center=ProfitCenter.TAPROOM.value,
            product_sku="BEER-IPA-KEG-001",
            product_name="IPA House Keg",
            origin_type="house",
            quantity=10.0,
            unit_measure="KEGS",
            unit_cost=500.00,
            unit_transfer_price=575.00,
            total_cost=5000.00,
            total_transfer_price=5750.00,
            factory_revenue=5750.00,
            factory_profit=750.00,
            taproom_cogs=5750.00,
            markup_percentage=15.00
        )
        
        db_session.add(transfer)
        db_session.commit()
        db_session.refresh(transfer)
        
        assert transfer.id is not None
        assert transfer.from_profit_center == "factory"
        assert transfer.to_profit_center == "taproom"
        assert float(transfer.factory_profit) == 750.00
    
    def test_factory_margin_percentage(self, db_session):
        """Test factory margin calculation."""
        transfer = InternalTransfer(
            from_profit_center="factory",
            to_profit_center="taproom",
            product_sku="TEST",
            product_name="Test Product",
            origin_type="house",
            quantity=10.0,
            unit_measure="KEGS",
            unit_cost=500.00,
            unit_transfer_price=575.00,
            total_cost=5000.00,
            total_transfer_price=5750.00,
            factory_revenue=5750.00,
            factory_profit=750.00,  # 750/5000 = 15%
            taproom_cogs=5750.00,
            markup_percentage=15.00
        )
        
        db_session.add(transfer)
        db_session.commit()
        
        # 750 / 5000 × 100 = 15%
        assert transfer.factory_margin_percentage == 15.00
    
    def test_passthrough_transfer(self, db_session):
        """Test guest beer passthrough (0% margin)."""
        transfer = InternalTransfer(
            from_profit_center="factory",
            to_profit_center="taproom",
            product_sku="GUEST-PALE",
            product_name="Guest Pale Ale",
            origin_type="guest",
            quantity=5.0,
            unit_measure="KEGS",
            unit_cost=300.00,
            unit_transfer_price=300.00,  # Passthrough
            total_cost=1500.00,
            total_transfer_price=1500.00,
            factory_revenue=1500.00,
            factory_profit=0.00,  # No profit
            taproom_cogs=1500.00,
            markup_percentage=0.00
        )
        
        db_session.add(transfer)
        db_session.commit()
        
        assert float(transfer.factory_profit) == 0.00
        assert transfer.factory_margin_percentage == 0.00
