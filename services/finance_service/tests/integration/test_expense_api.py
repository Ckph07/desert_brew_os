"""
Integration tests for Expense API.
"""
import pytest


class TestExpenseAPI:
    """Test expense CRUD endpoints."""

    def test_create_expense_supplier(self, client):
        """Test creating a supplier payment expense."""
        response = client.post("/api/v1/finance/expenses", json={
            "expense_type": "supplier_payment",
            "category": "raw_materials",
            "reference_id": "F-2026-033",
            "description": "Pago a Malteurop — Factura F-2026-033",
            "amount": 12500.00,
            "payment_method": "transfer",
            "profit_center": "factory",
            "supplier_name": "Malteurop México",
            "paid_by": "Contabilidad",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["expense_type"] == "supplier_payment"
        assert data["amount"] == 12500.00
        assert data["supplier_name"] == "Malteurop México"

    def test_create_expense_payroll(self, client):
        """Test payroll expense."""
        response = client.post("/api/v1/finance/expenses", json={
            "expense_type": "payroll",
            "category": "payroll",
            "reference_id": "NOM-2026-FEB-01",
            "description": "Nómina quincena 1 febrero 2026",
            "amount": 25000.00,
            "payment_method": "transfer",
            "profit_center": "general",
            "paid_by": "RH",
        })
        assert response.status_code == 201
        assert response.json()["category"] == "payroll"

    def test_create_expense_utility(self, client):
        """Test utility bill expense."""
        response = client.post("/api/v1/finance/expenses", json={
            "expense_type": "utility",
            "category": "energy",
            "description": "CFE — Recibo febrero 2026",
            "amount": 8000.00,
            "payment_method": "transfer",
            "profit_center": "factory",
        })
        assert response.status_code == 201

    def test_list_expenses(self, client):
        """Test listing expenses with filters."""
        client.post("/api/v1/finance/expenses", json={
            "expense_type": "supplier_payment", "category": "raw_materials",
            "description": "Malt", "amount": 5000.00,
            "payment_method": "transfer", "profit_center": "factory",
            "supplier_name": "Malteurop",
        })
        client.post("/api/v1/finance/expenses", json={
            "expense_type": "payroll", "category": "payroll",
            "description": "Nómina", "amount": 25000.00,
            "payment_method": "transfer", "profit_center": "general",
        })

        # List all
        response = client.get("/api/v1/finance/expenses")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Filter by supplier
        response = client.get("/api/v1/finance/expenses?supplier_name=Malteurop")
        assert len(response.json()) == 1

        # Filter by profit center
        response = client.get("/api/v1/finance/expenses?profit_center=factory")
        assert len(response.json()) == 1

    def test_update_expense(self, client):
        """Test updating an expense."""
        create = client.post("/api/v1/finance/expenses", json={
            "expense_type": "purchase", "category": "packaging",
            "description": "Barriles desechables", "amount": 4250.00,
            "payment_method": "card", "profit_center": "factory",
        })
        expense_id = create.json()["id"]

        response = client.patch(f"/api/v1/finance/expenses/{expense_id}", json={
            "amount": 4500.00,
            "notes": "Se agregaron 5 barriles más"
        })
        assert response.status_code == 200
        assert response.json()["amount"] == 4500.00

    def test_delete_expense(self, client):
        """Test deleting an expense."""
        create = client.post("/api/v1/finance/expenses", json={
            "expense_type": "other", "category": "other",
            "description": "Test delete", "amount": 100.00,
            "payment_method": "cash", "profit_center": "taproom",
        })
        expense_id = create.json()["id"]

        response = client.delete(f"/api/v1/finance/expenses/{expense_id}")
        assert response.status_code == 204

    def test_expense_summary(self, client):
        """Test expense summary by category."""
        client.post("/api/v1/finance/expenses", json={
            "expense_type": "supplier_payment", "category": "raw_materials",
            "description": "Malt", "amount": 12000.00,
            "payment_method": "transfer", "profit_center": "factory",
        })
        client.post("/api/v1/finance/expenses", json={
            "expense_type": "utility", "category": "energy",
            "description": "Luz", "amount": 8000.00,
            "payment_method": "transfer", "profit_center": "factory",
        })
        client.post("/api/v1/finance/expenses", json={
            "expense_type": "payroll", "category": "payroll",
            "description": "Nómina", "amount": 25000.00,
            "payment_method": "transfer", "profit_center": "general",
        })

        response = client.get("/api/v1/finance/expenses/summary?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["total_expenses"] == 45000.00
        assert data["count"] == 3
        assert data["by_category"]["raw_materials"] == 12000.00
        assert data["by_category"]["energy"] == 8000.00
        assert data["by_category"]["payroll"] == 25000.00

    def test_expense_not_found(self, client):
        """Test 404 for non-existent expense."""
        response = client.get("/api/v1/finance/expenses/9999")
        assert response.status_code == 404
