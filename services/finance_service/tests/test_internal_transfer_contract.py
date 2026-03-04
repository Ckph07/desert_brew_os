from decimal import Decimal

def test_internal_transfer_requires_product_sku(client, seeded_pricing_rules):
    payload = {
        "from_profit_center": "factory",
        "to_profit_center": "taproom",
        "product_name": "IPA Keg",
        "origin_type": "house",
        "quantity": 5,
        "unit_measure": "KEGS",
        "unit_cost": 42.0,
    }
    resp = client.post("/api/v1/finance/internal-transfers", json=payload)
    assert resp.status_code == 422


def test_internal_transfer_success(client, seeded_pricing_rules):
    payload = {
        "from_profit_center": "factory",
        "to_profit_center": "taproom",
        "product_sku": "BEER-IPA-KEG",
        "product_name": "IPA Keg",
        "origin_type": "house",
        "quantity": 5,
        "unit_measure": "KEGS",
        "unit_cost": 42.0,
    }
    resp = client.post("/api/v1/finance/internal-transfers", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["product_sku"] == "BEER-IPA-KEG"
    assert data["from_profit_center"] == "factory"
    assert Decimal(str(data["quantity"])) == Decimal("5")
    assert data["unit_transfer_price"] >= data["unit_cost"]
