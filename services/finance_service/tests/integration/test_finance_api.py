"""
Integration tests for Finance API endpoints.
"""
import pytest


class TestFinanceAPI:
    """Test finance endpoints."""
    
    def test_get_pricing_rules(self, client, seeded_pricing_rules):
        """Test getting all pricing rules."""
        response = client.get("/api/v1/finance/pricing-rules")
        
        assert response.status_code == 200
        rules = response.json()
        assert len(rules) == 4
        
        # Verify HOUSE rule
        house_rule = next((r for r in rules if r['origin_type'] == 'house'), None)
        assert house_rule is not None
        assert house_rule['markup_percentage'] == 15.00
        assert house_rule['strategy'] == 'cost_plus'
    
    def test_calculate_transfer_price_house(self, client, seeded_pricing_rules):
        """Test transfer price calculation API."""
        response = client.post(
            "/api/v1/finance/calculate-transfer-price",
            params={"origin_type": "house", "unit_cost": 500.00}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['origin_type'] == 'house'
        assert data['unit_cost'] == 500.00
        assert data['unit_transfer_price'] == 575.00  # 500 × 1.15
        assert data['markup_percentage'] == 15.00
        assert data['strategy'] == 'cost_plus'
    
    def test_calculate_transfer_price_guest(self, client, seeded_pricing_rules):
        """Test guest beer calculation (passthrough)."""
        response = client.post(
            "/api/v1/finance/calculate-transfer-price",
            params={"origin_type": "guest", "unit_cost": 300.00}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['unit_transfer_price'] == 300.00  # Passthrough
        assert data['markup_percentage'] == 0.00
    
    def test_calculate_transfer_price_unknown_origin(self, client):
        """Test error for unknown origin type."""
        response = client.post(
            "/api/v1/finance/calculate-transfer-price",
            params={"origin_type": "unknown", "unit_cost": 100.00}
        )
        
        assert response.status_code == 404
    
    def test_create_internal_transfer(self, client, seeded_pricing_rules):
        """Test creating internal transfer."""
        transfer_data = {
            "from_profit_center": "factory",
            "to_profit_center": "taproom",
            "product_sku": "BEER-IPA-KEG-001",
            "product_name": "IPA House Keg 50L",
            "origin_type": "house",
            "quantity": 10.0,
            "unit_measure": "KEGS",
            "unit_cost": 500.00,
            "notes": "Weekly transfer"
        }
        
        response = client.post(
            "/api/v1/finance/internal-transfers",
            json=transfer_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data['product_sku'] == "BEER-IPA-KEG-001"
        assert data['quantity'] == 10.0
        assert data['unit_cost'] == 500.00
        assert data['unit_transfer_price'] == 575.00  # Auto-calculated
        assert data['total_cost'] == 5000.00
        assert data['total_transfer_price'] == 5750.00
        assert data['factory_profit'] == 750.00
        assert data['taproom_cogs'] == 5750.00
        assert 'id' in data
    
    def test_create_transfer_guest_beer(self, client, seeded_pricing_rules):
        """Test guest beer transfer (no factory profit)."""
        transfer_data = {
            "from_profit_center": "factory",
            "to_profit_center": "taproom",
            "product_sku": "GUEST-PALE-KEG",
            "product_name": "Guest Pale Ale",
            "origin_type": "guest",
            "quantity": 5.0,
            "unit_measure": "KEGS",
            "unit_cost": 300.00
        }
        
        response = client.post(
            "/api/v1/finance/internal-transfers",
            json=transfer_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data['unit_transfer_price'] == 300.00  # Passthrough
        assert data['factory_profit'] == 0.00  # No profit
    
    def test_list_internal_transfers(self, client, seeded_pricing_rules):
        """Test listing transfers."""
        # Create transfers
        for i in range(3):
            client.post("/api/v1/finance/internal-transfers", json={
                "from_profit_center": "factory",
                "to_profit_center": "taproom",
                "product_sku": f"SKU-{i}",
                "product_name": f"Product {i}",
                "origin_type": "house",
                "quantity": 10.0,
                "unit_measure": "KEGS",
                "unit_cost": 500.00
            })
        
        # List all
        response = client.get("/api/v1/finance/internal-transfers")
        
        assert response.status_code == 200
        transfers = response.json()
        assert len(transfers) == 3
    
    def test_filter_transfers_by_origin(self, client, seeded_pricing_rules):
        """Test filtering transfers by origin type."""
        # Create house transfer
        client.post("/api/v1/finance/internal-transfers", json={
            "from_profit_center": "factory",
            "to_profit_center": "taproom",
            "product_sku": "HOUSE-SKU",
            "product_name": "House Beer",
            "origin_type": "house",
            "quantity": 10.0,
            "unit_measure": "KEGS",
            "unit_cost": 500.00
        })
        
        # Create guest transfer
        client.post("/api/v1/finance/internal-transfers", json={
            "from_profit_center": "factory",
            "to_profit_center": "taproom",
            "product_sku": "GUEST-SKU",
            "product_name": "Guest Beer",
            "origin_type": "guest",
            "quantity": 5.0,
            "unit_measure": "KEGS",
            "unit_cost": 300.00
        })
        
        # Filter by HOUSE
        response = client.get("/api/v1/finance/internal-transfers?origin_type=house")
        
        assert response.status_code == 200
        transfers = response.json()
        assert len(transfers) == 1
        assert transfers[0]['origin_type'] == 'house'
    
    def test_profit_center_summary_factory(self, client, seeded_pricing_rules):
        """Test factory P&L summary."""
        # Create transfer
        client.post("/api/v1/finance/internal-transfers", json={
            "from_profit_center": "factory",
            "to_profit_center": "taproom",
            "product_sku": "SKU-1",
            "product_name": "Product",
            "origin_type": "house",
            "quantity": 10.0,
            "unit_measure": "KEGS",
            "unit_cost": 500.00
        })
        
        # Get factory summary
        response = client.get("/api/v1/finance/profit-center/factory/summary?days=30")
        
        assert response.status_code == 200
        summary = response.json()
        
        assert summary['profit_center'] == 'factory'
        assert summary['total_revenue'] == 5750.00  # 10 × 575
        assert summary['total_cogs'] == 5000.00     # 10 × 500
        assert summary['total_profit'] == 750.00    # 5750 - 5000
        assert summary['profit_margin_percentage'] == 13.04  # 750/5750 × 100
        assert summary['transfer_count'] == 1
