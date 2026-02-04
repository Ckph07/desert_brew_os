"""
Unit tests for CommissionTier model.
"""
import pytest
from models.commission_tier import CommissionTier


class TestCommissionTierModel:
    """Test CommissionTier model."""
    
    def test_create_commission_tier(self, db_session):
        """Test creating a commission tier."""
        tier = CommissionTier(
            name="Test Tier",
            min_monthly_liters=100.0,
            commission_rate_per_liter=1.75,
            description="Test tier",
            badge_color="blue",
            is_active=True
        )
        
        db_session.add(tier)
        db_session.commit()
        db_session.refresh(tier)
        
        assert tier.id is not None
        assert tier.name == "Test Tier"
        assert float(tier.min_monthly_liters) == 100.0
        assert float(tier.commission_rate_per_liter) == 1.75
    
    def test_calculate_commission(self, db_session):
        """Test commission calculation method."""
        tier = CommissionTier(
            name="Gold",
            min_monthly_liters=200.0,
            commission_rate_per_liter=2.00,
            description="Gold tier",
            badge_color="gold",
            is_active=True
        )
        
        # 350 liters at $2.00/L = $700
        commission = tier.calculate_commission(350.0)
        assert commission == 700.0
        
        # 150 liters at $2.00/L = $300
        commission = tier.calculate_commission(150.0)
        assert commission == 300.0
    
    def test_display_rate(self, db_session):
        """Test formatted rate display."""
        tier = CommissionTier(
            name="Platinum",
            min_monthly_liters=500.0,
            commission_rate_per_liter=2.50,
            description="Platinum tier",
            badge_color="platinum",
            is_active=True
        )
        
        assert tier.display_rate == "$2.50/L"
    
    def test_unique_name_constraint(self, db_session):
        """Test that tier name must be unique."""
        tier1 = CommissionTier(
            name="Gold",
            min_monthly_liters=200.0,
            commission_rate_per_liter=2.00,
            is_active=True
        )
        
        tier2 = CommissionTier(
            name="Gold",  # Duplicate name
            min_monthly_liters=300.0,
            commission_rate_per_liter=2.50,
            is_active=True
        )
        
        db_session.add(tier1)
        db_session.commit()
        
        db_session.add(tier2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_inactive_tier(self, db_session):
        """Test inactive tier handling."""
        tier = CommissionTier(
            name="Deprecated",
            min_monthly_liters=100.0,
            commission_rate_per_liter=1.00,
            is_active=False  # Inactive
        )
        
        db_session.add(tier)
        db_session.commit()
        
        assert tier.is_active is False
