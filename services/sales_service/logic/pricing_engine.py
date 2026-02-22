"""
Pricing Engine - Margin comparison logic.

Purpose: Compare fixed (manual) prices vs theoretical (OS-calculated) prices
to identify margin opportunities and pricing inefficiencies.
"""
from decimal import Decimal
from typing import Optional


class PricingEngine:
    """
    Calculates and compares margins between fixed and theoretical pricing.

    Business Context:
    - fixed_price: What the business actually charges (set by owner)
    - theoretical_price: What the OS calculates (FIFO cost + transfer pricing + markup)
    - A positive delta means fixed price yields HIGHER margin than theoretical
    - A negative delta means the business is undercharging vs. theoretical
    """

    @staticmethod
    def calculate_margin(price: Optional[float], cost: Optional[float]) -> Optional[float]:
        """Calculate margin percentage: (price - cost) / price × 100."""
        if not price or not cost or price == 0:
            return None
        return round(float((Decimal(str(price)) - Decimal(str(cost))) / Decimal(str(price)) * 100), 2)

    @staticmethod
    def calculate_margins(product) -> dict:
        """
        Full margin comparison for a product.

        Returns:
            {
                "cost_per_unit": float,
                "fixed_price": float,
                "theoretical_price": float,
                "fixed_margin_pct": float,
                "theoretical_margin_pct": float,
                "margin_delta_pct": float,
                "channel_margins": {
                    "taproom": {"price": 130.0, "margin_pct": 83.4},
                    "distributor": {"price": 109.44, "margin_pct": 80.3},
                    ...
                }
            }
        """
        cost = float(product.cost_per_unit) if product.cost_per_unit else None

        fixed_margin = PricingEngine.calculate_margin(
            float(product.fixed_price) if product.fixed_price else None,
            cost,
        )
        theoretical_margin = PricingEngine.calculate_margin(
            float(product.theoretical_price) if product.theoretical_price else None,
            cost,
        )

        delta = None
        if fixed_margin is not None and theoretical_margin is not None:
            delta = round(fixed_margin - theoretical_margin, 2)

        # Per-channel margins
        channels = {}
        channel_fields = {
            "taproom": product.price_taproom,
            "distributor": product.price_distributor,
            "on_premise": product.price_on_premise,
            "off_premise": product.price_off_premise,
            "ecommerce": product.price_ecommerce,
        }

        for channel_name, channel_price in channel_fields.items():
            if channel_price:
                price_val = float(channel_price)
                margin = PricingEngine.calculate_margin(price_val, cost)
                channels[channel_name] = {
                    "price": price_val,
                    "cost": cost,
                    "margin_pct": margin,
                }

        return {
            "cost_per_unit": cost,
            "fixed_price": float(product.fixed_price) if product.fixed_price else None,
            "theoretical_price": float(product.theoretical_price) if product.theoretical_price else None,
            "fixed_margin_pct": fixed_margin,
            "theoretical_margin_pct": theoretical_margin,
            "margin_delta_pct": delta,
            "channel_margins": channels,
        }
