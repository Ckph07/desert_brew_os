"""
Seed data for Transfer Pricing Rules.

Creates pricing rules for all origin types:
- HOUSE: COST_PLUS with 15% markup
- GUEST: PASSTHROUGH with 0% markup
- COMMERCIAL: PASSTHROUGH with 0% markup
- MERCHANDISE: FIXED_MARKUP with 25% markup
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
from models.transfer_pricing_rule import TransferPricingRule, PricingStrategy

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://desertbrew:brewmaster2024@localhost:5432/desertbrew_finance"
)

def seed_pricing_rules():
    """Seed transfer pricing rules."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        existing = db.query(TransferPricingRule).count()
        if existing > 0:
            print(f"Pricing rules already seeded ({existing} rules exist)")
            return
        
        rules = [
            TransferPricingRule(
                origin_type="house",
                strategy=PricingStrategy.COST_PLUS.value,
                markup_percentage=15.00,
                rule_name="HOUSE Beer - Factory Margin",
                description="Factory earns 15% margin on own production. Transfer Price = Cost × 1.15",
                is_active=True
            ),
            TransferPricingRule(
                origin_type="guest",
                strategy=PricingStrategy.PASSTHROUGH.value,
                markup_percentage=0.00,
                rule_name="GUEST Craft - 3PL Passthrough",
                description="Factory acts as 3PL for guest breweries. Transfer Price = Cost × 1.00",
                is_active=True
            ),
            TransferPricingRule(
                origin_type="commercial",
                strategy=PricingStrategy.PASSTHROUGH.value,
                markup_percentage=0.00,
                rule_name="COMMERCIAL - Logistics Passthrough",
                description="Factory acts as logistics for commercial beer. Transfer Price = Cost × 1.00",
                is_active=True
            ),
            TransferPricingRule(
                origin_type="merchandise",
                strategy=PricingStrategy.FIXED_MARKUP.value,
                markup_percentage=25.00,
                rule_name="MERCHANDISE - Retail Markup",
                description="Factory markup on merchandise. Transfer Price = Cost × 1.25",
                is_active=True
            ),
        ]
        
        db.add_all(rules)
        db.commit()
        
        print(f"✅ Seeded {len(rules)} transfer pricing rules successfully")
        for rule in rules:
            print(f"   - {rule.origin_type.upper():12} → {rule.strategy:15} ({rule.markup_percentage:5.2f}%)")
        
    except Exception as e:
        print(f"❌ Error seeding pricing rules: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding Transfer Pricing Rules...")
    seed_pricing_rules()
