"""
Unit tests for BeerSmith parser.
"""
import pytest
import os
from logic.beersmith_parser import BeerSmithParser


class TestBeerSmithParser:
    """Test BeerSmith XML parser."""
    
    def test_parse_sample_ipa(self):
        """Test parsing sample IPA recipe."""
        # Get path to sample file
        test_dir = os.path.dirname(os.path.dirname(__file__))
        sample_path = os.path.join(test_dir, 'fixtures', 'sample_ipa.bsmx')
        
        recipe = BeerSmithParser.parse_file(sample_path)
        
        # Verify basic metadata
        assert recipe.name == "American IPA"
        assert recipe.style == "American IPA"
        assert recipe.batch_size_liters == 20.0
        assert recipe.brewer == "Desert Brew Co"
        
        # Verify calculated values
        assert recipe.expected_og == 1.065
        assert recipe.expected_fg == 1.012
        assert recipe.expected_abv == 6.96
        assert recipe.ibu == 65.0
        assert recipe.color_srm == 8.5
        assert recipe.brewhouse_efficiency == 75.0
    
    def test_parse_fermentables(self):
        """Test fermentables parsing."""
        test_dir = os.path.dirname(os.path.dirname(__file__))
        sample_path = os.path.join(test_dir, 'fixtures', 'sample_ipa.bsmx')
        
        recipe = BeerSmithParser.parse_file(sample_path)
        
        assert len(recipe.fermentables) == 2
        
        # Check Maris Otter
        maris = recipe.fermentables[0]
        assert maris['name'] == "Pale Malt, Maris Otter"
        assert maris['amount_kg'] == 5.0
        assert maris['color_srm'] == 3.0
        
        # Check Crystal
        crystal = recipe.fermentables[1]
        assert crystal['name'] == "Caramel/Crystal Malt - 40L"
        assert crystal['amount_kg'] == 0.5
    
    def test_parse_hops(self):
        """Test hops parsing."""
        test_dir = os.path.dirname(os.path.dirname(__file__))
        sample_path = os.path.join(test_dir, 'fixtures', 'sample_ipa.bsmx')
        
        recipe = BeerSmithParser.parse_file(sample_path)
        
        assert len(recipe.hops) == 3
        
        # Check Cascade (60 min boil)
        cascade = recipe.hops[0]
        assert cascade['name'] == "Cascade"
        assert cascade['amount_g'] == 50.0  # Converted from 0.050 kg
        assert cascade['time_min'] == 60.0
        assert cascade['use'] == "Boil"
        assert cascade['alpha_acid'] == 5.5
        
        # Check Citra (dry hop)
        citra = recipe.hops[2]
        assert citra['name'] == "Citra"
        assert citra['use'] == "Dry Hop"
    
    def test_parse_yeast(self):
        """Test yeast parsing."""
        test_dir = os.path.dirname(os.path.dirname(__file__))
        sample_path = os.path.join(test_dir, 'fixtures', 'sample_ipa.bsmx')
        
        recipe = BeerSmithParser.parse_file(sample_path)
        
        assert len(recipe.yeast) == 1
        
        yeast = recipe.yeast[0]
        assert yeast['name'] == "Safale US-05"
        assert yeast['lab'] == "Fermentis"
        assert yeast['product_id'] == "US-05"
        assert yeast['type'] == "Ale"
    
    def test_recipe_properties(self):
        """Test recipe calculated properties."""
        test_dir = os.path.dirname(os.path.dirname(__file__))
        sample_path = os.path.join(test_dir, 'fixtures', 'sample_ipa.bsmx')
        
        recipe = BeerSmithParser.parse_file(sample_path)
        
        # Test total_fermentables_kg property
        assert recipe.total_fermentables_kg == 5.5  # 5 + 0.5
        
        # Test total_hops_g property
        assert recipe.total_hops_g == 120.0  # 50 + 30 + 40
