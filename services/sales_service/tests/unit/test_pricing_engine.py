"""
Unit tests for PricingEngine logic.
"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from logic.pricing_engine import PricingEngine


class TestPricingEngine:
    """Test margin calculation logic."""

    def test_calculate_margin_normal(self):
        """Test margin calculation with valid values."""
        margin = PricingEngine.calculate_margin(100.0, 60.0)
        assert margin == 40.0  # (100-60)/100 × 100

    def test_calculate_margin_zero_price(self):
        """Test margin with zero price returns None."""
        margin = PricingEngine.calculate_margin(0, 60.0)
        assert margin is None

    def test_calculate_margin_no_cost(self):
        """Test margin with no cost returns None."""
        margin = PricingEngine.calculate_margin(100.0, None)
        assert margin is None

    def test_calculate_margins_full(self):
        """Test full margin comparison with product mock."""
        product = MagicMock()
        product.fixed_price = Decimal("109.44")
        product.theoretical_price = Decimal("95.00")
        product.cost_per_unit = Decimal("21.54")
        product.price_taproom = Decimal("130.00")
        product.price_distributor = Decimal("109.44")
        product.price_on_premise = None
        product.price_off_premise = None
        product.price_ecommerce = None

        result = PricingEngine.calculate_margins(product)

        assert result["fixed_margin_pct"] is not None
        assert result["theoretical_margin_pct"] is not None
        assert result["margin_delta_pct"] is not None
        assert result["fixed_margin_pct"] > result["theoretical_margin_pct"]
        assert "taproom" in result["channel_margins"]
        assert "distributor" in result["channel_margins"]
        assert result["channel_margins"]["taproom"]["margin_pct"] > 0
