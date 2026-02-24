"""
Integration tests for Income API.
"""
import pytest


class TestIncomeAPI:
    """Test income CRUD endpoints."""

    def test_create_income(self, client):
        """Test creating an income record."""
        response = client.post("/api/v1/finance/incomes", json={
            "income_type": "sales_note",
            "category": "beer_sales",
            "reference_id": "NV-2026-042",
            "description": "Nota #NV-2026-042 — Cliente Pepe, 3 pintas IPA",
            "amount": 450.00,
            "payment_method": "card",
            "profit_center": "taproom",
            "received_by": "Carlos",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["income_type"] == "sales_note"
        assert data["amount"] == 450.00
        assert data["profit_center"] == "taproom"

    def test_create_income_cash_sale(self, client):
        """Test cash sale income."""
        response = client.post("/api/v1/finance/incomes", json={
            "income_type": "cash_sale",
            "category": "merch_sales",
            "description": "Venta de 2 gorras + 1 playera",
            "amount": 850.00,
            "payment_method": "cash",
            "profit_center": "taproom",
        })
        assert response.status_code == 201
        assert response.json()["category"] == "merch_sales"

    def test_list_incomes(self, client):
        """Test listing incomes with filters."""
        # Create 2 incomes
        client.post("/api/v1/finance/incomes", json={
            "income_type": "sales_note",
            "category": "beer_sales",
            "description": "Venta cerveza 1",
            "amount": 300.00,
            "payment_method": "card",
            "profit_center": "taproom",
        })
        client.post("/api/v1/finance/incomes", json={
            "income_type": "cash_sale",
            "category": "food_sales",
            "description": "Venta comida 1",
            "amount": 150.00,
            "payment_method": "cash",
            "profit_center": "taproom",
        })

        # List all
        response = client.get("/api/v1/finance/incomes")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Filter by category
        response = client.get("/api/v1/finance/incomes?category=beer_sales")
        assert len(response.json()) == 1

    def test_get_income(self, client):
        """Test getting income detail."""
        create = client.post("/api/v1/finance/incomes", json={
            "income_type": "sales_note",
            "category": "beer_sales",
            "description": "Test income",
            "amount": 500.00,
            "payment_method": "transfer",
            "profit_center": "taproom",
        })
        income_id = create.json()["id"]

        response = client.get(f"/api/v1/finance/incomes/{income_id}")
        assert response.status_code == 200
        assert response.json()["amount"] == 500.00

    def test_update_income(self, client):
        """Test updating an income record."""
        create = client.post("/api/v1/finance/incomes", json={
            "income_type": "sales_note",
            "category": "beer_sales",
            "description": "Original",
            "amount": 300.00,
            "payment_method": "cash",
            "profit_center": "taproom",
        })
        income_id = create.json()["id"]

        response = client.patch(f"/api/v1/finance/incomes/{income_id}", json={
            "amount": 350.00,
            "notes": "Corregido — incluía propina"
        })
        assert response.status_code == 200
        assert response.json()["amount"] == 350.00

    def test_delete_income(self, client):
        """Test deleting an income record."""
        create = client.post("/api/v1/finance/incomes", json={
            "income_type": "sales_note",
            "category": "beer_sales",
            "description": "To delete",
            "amount": 100.00,
            "payment_method": "cash",
            "profit_center": "taproom",
        })
        income_id = create.json()["id"]

        response = client.delete(f"/api/v1/finance/incomes/{income_id}")
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/api/v1/finance/incomes/{income_id}")
        assert response.status_code == 404

    def test_income_summary(self, client):
        """Test income summary by category."""
        client.post("/api/v1/finance/incomes", json={
            "income_type": "sales_note", "category": "beer_sales",
            "description": "Beer 1", "amount": 500.00,
            "payment_method": "card", "profit_center": "taproom",
        })
        client.post("/api/v1/finance/incomes", json={
            "income_type": "cash_sale", "category": "merch_sales",
            "description": "Merch 1", "amount": 200.00,
            "payment_method": "cash", "profit_center": "taproom",
        })

        response = client.get("/api/v1/finance/incomes/summary?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 700.00
        assert data["count"] == 2
        assert data["by_category"]["beer_sales"] == 500.00
        assert data["by_category"]["merch_sales"] == 200.00

    def test_income_not_found(self, client):
        """Test 404 for non-existent income."""
        response = client.get("/api/v1/finance/incomes/9999")
        assert response.status_code == 404
