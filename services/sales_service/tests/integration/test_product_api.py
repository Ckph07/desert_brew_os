"""
Integration tests for Product Catalog API endpoints.
"""
import pytest


class TestProductAPI:
    """Test product catalog CRUD endpoints."""

    def test_create_product(self, client, sample_product_data):
        """Test creating a product with dual pricing."""
        response = client.post("/api/v1/sales/products", json=sample_product_data)
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "BEER-IPA-COAHUI-L"
        assert data["fixed_price"] == 109.44
        assert data["theoretical_price"] == 95.00
        assert data["cost_per_unit"] == 21.54
        assert data["fixed_margin_pct"] is not None
        assert data["theoretical_margin_pct"] is not None

    def test_duplicate_sku_rejected(self, client, sample_product_data):
        """Test that duplicate SKUs are rejected."""
        client.post("/api/v1/sales/products", json=sample_product_data)
        response = client.post("/api/v1/sales/products", json=sample_product_data)
        assert response.status_code == 409

    def test_list_products(self, client, sample_product_data):
        """Test listing products."""
        client.post("/api/v1/sales/products", json=sample_product_data)
        response = client.get("/api/v1/sales/products")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_product(self, client, sample_product_data):
        """Test getting product with margins."""
        create_resp = client.post("/api/v1/sales/products", json=sample_product_data)
        pid = create_resp.json()["id"]
        response = client.get(f"/api/v1/sales/products/{pid}")
        assert response.status_code == 200
        data = response.json()
        # Verify margin calculations
        assert data["fixed_margin_pct"] > 0
        assert data["theoretical_margin_pct"] > 0
        assert data["margin_delta_pct"] is not None

    def test_update_product(self, client, sample_product_data):
        """Test updating product."""
        create_resp = client.post("/api/v1/sales/products", json=sample_product_data)
        pid = create_resp.json()["id"]
        response = client.patch(
            f"/api/v1/sales/products/{pid}",
            json={"fixed_price": 120.00},
        )
        assert response.status_code == 200
        assert response.json()["fixed_price"] == 120.00

    def test_update_channel_prices_with_history(self, client, sample_product_data):
        """Test updating channel prices creates PriceHistory records."""
        create_resp = client.post("/api/v1/sales/products", json=sample_product_data)
        pid = create_resp.json()["id"]

        # Update prices
        response = client.patch(
            f"/api/v1/sales/products/{pid}/prices",
            json={
                "price_taproom": 140.00,
                "fixed_price": 115.00,
                "change_reason": "Price adjustment Q1 2026",
                "changed_by": "admin",
            },
        )
        assert response.status_code == 200
        assert response.json()["price_taproom"] == 140.00
        assert response.json()["fixed_price"] == 115.00

        # Check history
        hist_resp = client.get(f"/api/v1/sales/products/{pid}/price-history")
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) >= 2  # taproom + fixed

    def test_margin_report(self, client, sample_product_data):
        """Test margin comparison report."""
        # Create products
        client.post("/api/v1/sales/products", json=sample_product_data)

        lager = {**sample_product_data}
        lager["sku"] = "BEER-LAGER-VELA-L"
        lager["product_name"] = "Litro Velafrons (Mexican Pale Lager)"
        lager["fixed_price"] = 82.33
        lager["theoretical_price"] = 75.00
        lager["cost_per_unit"] = 18.00
        client.post("/api/v1/sales/products", json=lager)

        response = client.get("/api/v1/sales/products/margin-report")
        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 2
        assert data["avg_fixed_margin"] is not None
        assert data["avg_theoretical_margin"] is not None
        assert len(data["products"]) == 2

    def test_delete_product(self, client, sample_product_data):
        """Test soft-deleting a product."""
        create_resp = client.post("/api/v1/sales/products", json=sample_product_data)
        pid = create_resp.json()["id"]
        response = client.delete(f"/api/v1/sales/products/{pid}")
        assert response.status_code == 200

    def test_filter_by_origin(self, client, sample_product_data):
        """Test filtering products by origin_type."""
        client.post("/api/v1/sales/products", json=sample_product_data)
        response = client.get("/api/v1/sales/products?origin_type=HOUSE")
        assert response.status_code == 200
        assert len(response.json()) >= 1
