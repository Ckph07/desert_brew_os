"""
Recipe Model - Parsed from BeerSmith .bsmx files.

Stores recipe information for production planning.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import JSON
from database import Base
from datetime import datetime


class Recipe(Base):
    """
    Beer recipe from BeerSmith.
    
    Source: .bsmx XML file (BeerSmith 3 format)
    Usage: Template for ProductionBatch creation
    """
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True)
    
    # Recipe metadata
    name = Column(String(200), nullable=False)
    style = Column(String(100))  # e.g., "American IPA"
    brewer = Column(String(100))
    batch_size_liters = Column(Numeric(10, 2), nullable=False)
    
    # Ingredients (stored as JSON arrays)
    fermentables = Column(JSON, nullable=False)  # [{"name": "Maris Otter", "amount_kg": 5.0, "color_srm": 3}]
    hops = Column(JSON, nullable=False)          # [{"name": "Cascade", "amount_g": 50, "time_min": 60, "use": "Boil"}]
    yeast = Column(JSON, nullable=False)         # [{"name": "US-05", "amount": "1 packet"}]
    water_profile = Column(JSON)                 # {"ca": 50, "mg": 10, "na": 5, ...}
    
    # Mash schedule (optional, stored as JSON for Sprint 4)
    mash_steps = Column(JSON)  # [{"step": "Mash In", "temp_c": 67, "time_min": 60}]
    
    # Calculated values (from BeerSmith)
    expected_og = Column(Numeric(4, 3))  # Original Gravity (1.055)
    expected_fg = Column(Numeric(4, 3))  # Final Gravity (1.012)
    expected_abv = Column(Numeric(4, 2)) # Alcohol by Volume (5.5%)
    ibu = Column(Numeric(5, 1))          # International Bitterness Units
    color_srm = Column(Numeric(5, 1))    # Color (Standard Reference Method)
    
    # Efficiency
    brewhouse_efficiency = Column(Numeric(5, 2))  # 75.00%
    
    # Source file
    bsmx_file_path = Column(String(500))
    bsmx_file_name = Column(String(200))
    
    # Audit
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    imported_by_user_id = Column(Integer)
    
    # Notes
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Recipe(name='{self.name}', style='{self.style}', batch_size={self.batch_size_liters}L)>"
    
    @property
    def total_fermentables_kg(self) -> float:
        """Calculate total fermentables weight."""
        if not self.fermentables:
            return 0.0
        return sum(f.get('amount_kg', 0) for f in self.fermentables)
    
    @property
    def total_hops_g(self) -> float:
        """Calculate total hops weight."""
        if not self.hops:
            return 0.0
        return sum(h.get('amount_g', 0) for h in self.hops)
