"""
Seed data for Commission Tiers (Sprint 3).

Creates 4 tiers: Platinum, Gold, Silver, Bronze
Based on monthly volume thresholds.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
from models.commission_tier import CommissionTier

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://desertbrew:brewmaster2024@localhost:5432/desertbrew_sales"
)

def seed_commission_tiers():
    """Seed commission tier data."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if already seeded
        existing = db.query(CommissionTier).count()
        if existing > 0:
            print(f"Commission tiers already seeded ({existing} tiers exist)")
            return
        
        # Create tiers
        tiers = [
            CommissionTier(
                name="Platinum",
                min_monthly_liters=500.0,
                commission_rate_per_liter=2.50,
                description="Elite sellers >500L/month",
                badge_color="platinum",
                is_active=True
            ),
            CommissionTier(
                name="Gold",
               min_monthly_liters=200.0,
                commission_rate_per_liter=2.00,
                description="High performers 200-499L/month",
                badge_color="gold",
                is_active=True
            ),
            CommissionTier(
                name="Silver",
                min_monthly_liters=50.0,
                commission_rate_per_liter=1.50,
                description="Standard sellers 50-199L/month",
                badge_color="silver",
                is_active=True
            ),
            CommissionTier(
                name="Bronze",
                min_monthly_liters=0.0,
                commission_rate_per_liter=1.00,
                description="Entry level <50L/month",
                badge_color="bronze",
                is_active=True
            ),
        ]
        
        db.add_all(tiers)
        db.commit()
        
        print(f"✅ Seeded {len(tiers)} commission tiers successfully")
        for tier in tiers:
            print(f"   - {tier.name}: ${tier.commission_rate_per_liter}/L (min {tier.min_monthly_liters}L)")
        
    except Exception as e:
        print(f"❌ Error seeding commission tiers: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding Commission Tiers...")
    seed_commission_tiers()
