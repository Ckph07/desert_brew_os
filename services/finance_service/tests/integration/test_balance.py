"""
Integration tests for Balance and Cashflow endpoints.
"""
import pytest


class TestBalanceAPI:
    """Test balance and cashflow endpoints."""

    def _seed_data(self, client):
        """Helper to seed incomes and expenses."""
        # Incomes
        client.post("/api/v1/finance/incomes", json={
            "income_type": "sales_note", "category": "beer_sales",
            "description": "Beer sales week 1", "amount": 15000.00,
            "payment_method": "card", "profit_center": "taproom",
        })
        client.post("/api/v1/finance/incomes", json={
            "income_type": "cash_sale", "category": "merch_sales",
            "description": "Merch sales week 1", "amount": 3000.00,
            "payment_method": "cash", "profit_center": "taproom",
        })

        # Expenses
        client.post("/api/v1/finance/expenses", json={
            "expense_type": "supplier_payment", "category": "raw_materials",
            "description": "Malt purchase", "amount": 5000.00,
            "payment_method": "transfer", "profit_center": "factory",
        })
        client.post("/api/v1/finance/expenses", json={
            "expense_type": "payroll", "category": "payroll",
            "description": "Payroll", "amount": 8000.00,
            "payment_method": "transfer", "profit_center": "general",
        })

    def test_balance(self, client):
        """Test consolidated balance."""
        self._seed_data(client)

        response = client.get("/api/v1/finance/balance?days=30")
        assert response.status_code == 200
        data = response.json()

        assert data["total_income"] == 18000.00
        assert data["total_expenses"] == 13000.00
        assert data["net_profit"] == 5000.00
        assert data["income_by_category"]["beer_sales"] == 15000.00
        assert data["expenses_by_category"]["raw_materials"] == 5000.00
        assert data["expenses_by_category"]["payroll"] == 8000.00

    def test_balance_empty(self, client):
        """Test balance with no data."""
        response = client.get("/api/v1/finance/balance?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 0.0
        assert data["total_expenses"] == 0.0
        assert data["net_profit"] == 0.0

    def test_cashflow(self, client):
        """Test monthly cashflow."""
        self._seed_data(client)

        response = client.get("/api/v1/finance/cashflow?months=6")
        assert response.status_code == 200
        data = response.json()

        assert data["total_income"] == 18000.00
        assert data["total_expenses"] == 13000.00
        assert data["total_net"] == 5000.00
        assert len(data["months"]) >= 1

    def test_cashflow_empty(self, client):
        """Test cashflow with no data."""
        response = client.get("/api/v1/finance/cashflow?months=6")
        assert response.status_code == 200
        assert response.json()["total_net"] == 0.0
