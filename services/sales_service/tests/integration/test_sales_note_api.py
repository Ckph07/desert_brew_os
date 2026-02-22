"""
Integration tests for Sales Notes API endpoints.
"""
import pytest


class TestSalesNoteAPI:
    """Test sales notes CRUD and export endpoints."""

    def _create_client_and_product(self, client):
        """Helper to create test client and product."""
        cl = client.post("/api/v1/sales/clients", json={
            "business_name": "Hop Experience",
            "client_type": "B2B",
            "pricing_tier": "GOLD",
        }).json()

        prod = client.post("/api/v1/sales/products", json={
            "sku": "BEER-IPA-L",
            "product_name": "Litro Coahuilaceratops (Imperial Indian Pale Ale)",
            "category": "BEER_LITER",
            "origin_type": "HOUSE",
            "fixed_price": 109.44,
            "cost_per_unit": 21.54,
        }).json()

        return cl, prod

    def test_create_sales_note_no_taxes(self, client):
        """Test creating a sales note without taxes (most common case)."""
        cl, prod = self._create_client_and_product(client)

        response = client.post("/api/v1/sales/notes", json={
            "client_id": cl["id"],
            "client_name": "Hop Experience",
            "channel": "B2B",
            "payment_method": "TRANSFERENCIA",
            "include_taxes": False,
            "items": [
                {
                    "product_name": "Litro Carnotaurus (Amber Lager)",
                    "unit_measure": "LITROS",
                    "quantity": 18,
                    "unit_price": 77.44,
                },
                {
                    "product_name": "Litro Coahuilaceratops (Imperial Indian Pale Ale)",
                    "unit_measure": "LITROS",
                    "quantity": 18,
                    "unit_price": 109.44,
                },
                {
                    "product_name": "Barril Desechable 20L",
                    "unit_measure": "UNITS",
                    "quantity": 2,
                    "unit_price": 589.00,
                },
                {
                    "product_name": "Envío",
                    "unit_measure": "UNITS",
                    "quantity": 2,
                    "unit_price": 285.00,
                },
            ],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["note_number"] == "00000001"
        assert data["include_taxes"] is False
        assert data["ieps_total"] == 0.0
        assert data["iva_total"] == 0.0
        assert data["total_liters"] == 36.0
        assert len(data["items"]) == 4

        # Verify subtotal = total (no taxes)
        expected_subtotal = (18 * 77.44) + (18 * 109.44) + (2 * 589) + (2 * 285)
        assert data["subtotal"] == expected_subtotal
        assert data["total"] == expected_subtotal

    def test_create_sales_note_with_taxes(self, client):
        """Test creating a sales note WITH taxes (invoiced)."""
        response = client.post("/api/v1/sales/notes", json={
            "client_name": "Restaurant X",
            "channel": "B2B",
            "payment_method": "TRANSFERENCIA",
            "include_taxes": True,
            "items": [
                {
                    "product_name": "Litro IPA",
                    "unit_measure": "LITROS",
                    "quantity": 10,
                    "unit_price": 100.00,
                    "ieps_rate": 0.10,
                    "iva_rate": 0.16,
                },
            ],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["include_taxes"] is True
        assert data["subtotal"] == 1000.00
        assert data["ieps_total"] == 100.00  # 1000 × 0.10
        assert data["iva_total"] == 160.00   # 1000 × 0.16
        assert data["total"] == 1260.00      # 1000 + 100 + 160

    def test_list_sales_notes(self, client):
        """Test listing sales notes."""
        client.post("/api/v1/sales/notes", json={
            "client_name": "Test",
            "include_taxes": False,
            "items": [{"product_name": "IPA", "quantity": 1, "unit_price": 100}],
        })
        response = client.get("/api/v1/sales/notes")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_sales_note(self, client):
        """Test getting a specific sales note with items."""
        create_resp = client.post("/api/v1/sales/notes", json={
            "client_name": "Test Client",
            "include_taxes": False,
            "items": [{"product_name": "Lager", "quantity": 18, "unit_price": 82.33, "unit_measure": "LITROS"}],
        })
        note_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/sales/notes/{note_id}")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    def test_confirm_note(self, client):
        """Test confirming a draft note."""
        create_resp = client.post("/api/v1/sales/notes", json={
            "client_name": "Test",
            "include_taxes": False,
            "items": [{"product_name": "IPA", "quantity": 1, "unit_price": 100}],
        })
        note_id = create_resp.json()["id"]

        response = client.patch(f"/api/v1/sales/notes/{note_id}/confirm")
        assert response.status_code == 200
        assert response.json()["status"] == "CONFIRMED"
        assert response.json()["confirmed_at"] is not None

    def test_cannot_modify_confirmed_note(self, client):
        """Test that confirmed notes cannot be modified."""
        create_resp = client.post("/api/v1/sales/notes", json={
            "client_name": "Test",
            "include_taxes": False,
            "items": [{"product_name": "IPA", "quantity": 1, "unit_price": 100}],
        })
        note_id = create_resp.json()["id"]
        client.patch(f"/api/v1/sales/notes/{note_id}/confirm")

        # Try to update
        response = client.patch(
            f"/api/v1/sales/notes/{note_id}",
            json={"client_name": "Changed"},
        )
        assert response.status_code == 400

    def test_cancel_note(self, client):
        """Test cancelling a note."""
        create_resp = client.post("/api/v1/sales/notes", json={
            "client_name": "Test",
            "include_taxes": False,
            "items": [{"product_name": "IPA", "quantity": 1, "unit_price": 100}],
        })
        note_id = create_resp.json()["id"]
        response = client.patch(f"/api/v1/sales/notes/{note_id}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"

    def test_note_number_auto_increment(self, client):
        """Test note numbers auto-increment."""
        r1 = client.post("/api/v1/sales/notes", json={
            "client_name": "A",
            "include_taxes": False,
            "items": [{"product_name": "IPA", "quantity": 1, "unit_price": 100}],
        })
        r2 = client.post("/api/v1/sales/notes", json={
            "client_name": "B",
            "include_taxes": False,
            "items": [{"product_name": "Lager", "quantity": 1, "unit_price": 80}],
        })
        assert r1.json()["note_number"] == "00000001"
        assert r2.json()["note_number"] == "00000002"

    def test_filter_by_status(self, client):
        """Test filtering notes by status."""
        client.post("/api/v1/sales/notes", json={
            "client_name": "Test",
            "include_taxes": False,
            "items": [{"product_name": "IPA", "quantity": 1, "unit_price": 100}],
        })
        response = client.get("/api/v1/sales/notes?status=DRAFT")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_note_not_found(self, client):
        """Test 404 for non-existent note."""
        response = client.get("/api/v1/sales/notes/99999")
        assert response.status_code == 404
