"""
Integration tests for Client API endpoints.
"""
import pytest


class TestClientAPI:
    """Test client CRUD endpoints."""

    def test_create_client(self, client, sample_client_data):
        """Test creating a new client."""
        response = client.post("/api/v1/sales/clients", json=sample_client_data)
        assert response.status_code == 201
        data = response.json()
        assert data["business_name"] == "Bar La Herradura"
        assert data["client_code"].startswith("CLI-")
        assert data["pricing_tier"] == "GOLD"
        assert data["credit_limit"] == 50000.00
        assert data["current_balance"] == 0.0
        assert data["is_active"] is True

    def test_list_clients(self, client, sample_client_data):
        """Test listing clients."""
        client.post("/api/v1/sales/clients", json=sample_client_data)
        response = client.get("/api/v1/sales/clients")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_client(self, client, sample_client_data):
        """Test getting a specific client."""
        create_resp = client.post("/api/v1/sales/clients", json=sample_client_data)
        client_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/sales/clients/{client_id}")
        assert response.status_code == 200
        assert response.json()["business_name"] == "Bar La Herradura"

    def test_update_client(self, client, sample_client_data):
        """Test updating a client."""
        create_resp = client.post("/api/v1/sales/clients", json=sample_client_data)
        client_id = create_resp.json()["id"]
        response = client.patch(
            f"/api/v1/sales/clients/{client_id}",
            json={"pricing_tier": "PLATINUM", "credit_limit": 100000.00},
        )
        assert response.status_code == 200
        assert response.json()["pricing_tier"] == "PLATINUM"
        assert response.json()["credit_limit"] == 100000.00

    def test_delete_client(self, client, sample_client_data):
        """Test soft-deleting a client."""
        create_resp = client.post("/api/v1/sales/clients", json=sample_client_data)
        client_id = create_resp.json()["id"]
        response = client.delete(f"/api/v1/sales/clients/{client_id}")
        assert response.status_code == 200

        # Verify soft-deleted (not visible in active-only list)
        list_resp = client.get("/api/v1/sales/clients?active_only=true")
        ids = [c["id"] for c in list_resp.json()]
        assert client_id not in ids

    def test_get_client_balance(self, client, sample_client_data):
        """Test getting client balance with credit check."""
        create_resp = client.post("/api/v1/sales/clients", json=sample_client_data)
        client_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/sales/clients/{client_id}/balance")
        assert response.status_code == 200
        data = response.json()
        assert data["available_credit"] == 50000.00
        assert data["can_order"] is True
        assert data["blocking_reasons"] == []

    def test_filter_by_type(self, client, sample_client_data):
        """Test filtering clients by type."""
        client.post("/api/v1/sales/clients", json=sample_client_data)
        response = client.get("/api/v1/sales/clients?client_type=B2B")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_search_by_name(self, client, sample_client_data):
        """Test searching clients by name."""
        client.post("/api/v1/sales/clients", json=sample_client_data)
        response = client.get("/api/v1/sales/clients?search=Herradura")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_client_not_found(self, client):
        """Test 404 for non-existent client."""
        response = client.get("/api/v1/sales/clients/99999")
        assert response.status_code == 404
