"""
Integration tests for commission tier API endpoints.
"""
import pytest


class TestCommissionTierAPI:
    """Test commission tier endpoints."""
    
    def test_get_all_tiers(self, client, seeded_tiers):
        """Test getting all commission tiers."""
        response = client.get("/api/v1/sales/commission-tiers")
        
        assert response.status_code == 200
        tiers = response.json()
        assert len(tiers) == 4
        
        # Verify order (descending by min_monthly_liters)
        assert tiers[0]["name"] == "Platinum"
        assert tiers[1]["name"] == "Gold"
        assert tiers[2]["name"] == "Silver"
        assert tiers[3]["name"] == "Bronze"
    
    def test_get_active_tiers_only(self, client, db_session):
        """Test filtering for active tiers."""
        from models.commission_tier import CommissionTier
        
        # Add active tier
        active = CommissionTier(
            name="Active",
            min_monthly_liters=100.0,
            commission_rate_per_liter=1.50,
            is_active=True
        )
        
        # Add inactive tier
        inactive = CommissionTier(
            name="Inactive",
            min_monthly_liters=50.0,
            commission_rate_per_liter=1.00,
            is_active=False
        )
        
        db_session.add_all([active, inactive])
        db_session.commit()
        
        # Get only active
        response = client.get("/api/v1/sales/commission-tiers?active_only=true")
        
        assert response.status_code == 200
        tiers = response.json()
        assert len(tiers) == 1
        assert tiers[0]["name"] == "Active"
    
    def test_get_seller_tier_no_volume(self, client, seeded_tiers):
        """Test seller tier with zero volume."""
        response = client.get("/api/v1/sales/sellers/999/tier")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 999
        assert data["current_month_volume_liters"] == 0.0
        assert data["current_tier"] == "Bronze"  # Default tier
        assert data["commission_rate"] == 1.00
    
    def test_tier_structure(self, client, seeded_tiers):
        """Test tier response structure."""
        response = client.get("/api/v1/sales/commission-tiers")
        
        assert response.status_code == 200
        tiers = response.json()
        
        # Verify structure of first tier
        platinum = tiers[0]
        assert "id" in platinum
        assert "name" in platinum
        assert "min_monthly_liters" in platinum
        assert "commission_rate_per_liter" in platinum
        assert "description" in platinum
        assert "badge_color" in platinum
        assert "is_active" in platinum
        
        assert platinum["name"] == "Platinum"
        assert platinum["min_monthly_liters"] == 500.0
        assert platinum["commission_rate_per_liter"] == 2.50
