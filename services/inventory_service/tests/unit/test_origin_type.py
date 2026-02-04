"""
Unit tests for OriginType enum and finished product validation.
"""
import pytest
from models.finished_product_enums import OriginType
from models.finished_product import FinishedProductInventory


class TestOriginType:
    """Test OriginType enum."""
    
    def test_origin_type_values(self):
        """Test all OriginType enum values."""
        assert OriginType.HOUSE.value == "house"
        assert OriginType.GUEST.value == "guest"
        assert OriginType.COMMERCIAL.value == "commercial"
        assert OriginType.MERCHANDISE.value == "merchandise"
    
    def test_origin_type_membership(self):
        """Test enum membership."""
        assert "house" in [t.value for t in OriginType]
        assert "guest" in [t.value for t in OriginType]
        assert "invalid" not in [t.value for t in OriginType]


class TestFinishedProductOriginValidation:
    """Test FinishedProduct with origin_type field."""
    
    def test_create_house_product(self, db_session):
        """Test creating HOUSE origin product."""
        product = FinishedProductInventory(
            sku="HOUSE-IPA-KEG-001",
            product_name="IPA House Keg",
            product_type="OWN_PRODUCTION",
            category="BEER_KEG",
            origin_type="house",  # HOUSE origin
            production_batch_id=123,  # Required for HOUSE
            quantity=10.0,
            unit_measure="KEGS",
            cold_room_id="COLD_ROOM_A"
        )
        
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        
        assert product.origin_type == "house"
        assert product.production_batch_id == 123
    
    def test_create_guest_product(self, db_session):
        """Test creating GUEST origin product."""
        product = FinishedProductInventory(
            sku="GUEST-PALE-KEG-001",
            product_name="Guest Pale Ale",
            product_type="GUEST_CRAFT",
            category="BEER_KEG",
            origin_type="guest",
            guest_brewery_id=42,  # Guest brewery
            quantity=5.0,
            unit_measure="KEGS",
            cold_room_id="COLD_ROOM_B"
        )
        
        db_session.add(product)
        db_session.commit()
        
        assert product.origin_type == "guest"
        assert product.guest_brewery_id == 42
    
    def test_create_commercial_product(self, db_session):
        """Test creating COMMERCIAL origin product."""
        product = FinishedProductInventory(
            sku="COMM-CORONA-BOTTLE-001",
            product_name="Corona Extra 355ml",
            product_type="COMMERCIAL",
            category="BEER_BOTTLE",
            origin_type="commercial",
            supplier_id=10,
            quantity=240.0,  # 10 cases
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A"
        )
        
        db_session.add(product)
        db_session.commit()
        
        assert product.origin_type == "commercial"
        assert product.supplier_id == 10
    
    def test_create_merchandise(self, db_session):
        """Test creating MERCHANDISE origin product."""
        product = FinishedProductInventory(
            sku="MERCH-SHIRT-L-001",
            product_name="Desert Brew T-Shirt Large",
            product_type="MERCHANDISE",
            category="MERCH_SHIRT",
            origin_type="merchandise",
            quantity=50.0,
            unit_measure="UNITS",
            cold_room_id="WAREHOUSE"  # Room temp
        )
        
        db_session.add(product)
        db_session.commit()
        
        assert product.origin_type == "merchandise"
    
    def test_query_by_origin_type(self, db_session):
        """Test filtering products by origin_type."""
        # Create products
        house1 = FinishedProductInventory(
            sku="HOUSE-001", product_name="House Beer 1",
            product_type="OWN_PRODUCTION", category="BEER_KEG",
            origin_type="house", production_batch_id=1,
            quantity=5.0, unit_measure="KEGS", cold_room_id="COLD_ROOM_A"
        )
        
        house2 = FinishedProductInventory(
            sku="HOUSE-002", product_name="House Beer 2",
            product_type="OWN_PRODUCTION", category="BEER_KEG",
            origin_type="house", production_batch_id=2,
            quantity=8.0, unit_measure="KEGS", cold_room_id="COLD_ROOM_A"
        )
        
        guest1 = FinishedProductInventory(
            sku="GUEST-001", product_name="Guest Beer 1",
            product_type="GUEST_CRAFT", category="BEER_KEG",
            origin_type="guest", guest_brewery_id=10,
            quantity=3.0, unit_measure="KEGS", cold_room_id="COLD_ROOM_B"
        )
        
        db_session.add_all([house1, house2, guest1])
        db_session.commit()
        
        # Query HOUSE products
        house_products = db_session.query(FinishedProductInventory).filter_by(
            origin_type="house"
        ).all()
        
        assert len(house_products) == 2
        assert all(p.origin_type == "house" for p in house_products)
        
        # Query GUEST products
        guest_products = db_session.query(FinishedProductInventory).filter_by(
            origin_type="guest"
        ).all()
        
        assert len(guest_products) == 1
        assert guest_products[0].sku == "GUEST-001"
