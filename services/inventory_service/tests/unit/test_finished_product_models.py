"""
Unit tests for Finished Product models.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from models.finished_product import FinishedProductInventory
from models.cold_room_reading import ColdRoomReading
from models.product_movement import ProductMovement
from models.finished_product_enums import ProductType, ProductCategory, AvailabilityStatus


class TestFinishedProductInventory:
    """Tests for FinishedProductInventory model."""
    
    def test_create_own_production_beer(self):
        """Test creating own production beer product."""
        product = FinishedProductInventory(
            sku="BEER-IPA-COAHUI-BTL355",
            product_name="IPA Coahuilaceratops 355ml",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            production_batch_id=42,
            quantity=Decimal('240.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A",
            shelf_position="A3",
            unit_cost=Decimal('25.50'),
            best_before=datetime.utcnow() + timedelta(days=90)
        )
        
        assert product.sku == "BEER-IPA-COAHUI-BTL355"
        assert product.product_type == ProductType.OWN_PRODUCTION.value
        assert product.quantity == Decimal('240.00')
        assert product.production_batch_id == 42
    
    def test_create_commercial_beer(self):
        """Test creating commercial beer product."""
        product = FinishedProductInventory(
            sku="BEER-CORONA-BTL355",
            product_name="Corona Extra 355ml",
            product_type=ProductType.COMMERCIAL.value,
            category=ProductCategory.BEER_BOTTLE.value,
            supplier_id=10,
            quantity=Decimal('480.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_B",
            unit_cost=Decimal('15.50')
        )
        
        assert product.product_type == ProductType.COMMERCIAL.value
        assert product.supplier_id == 10
        assert product.production_batch_id is None
    
    def test_is_available_property(self):
        """Test is_available computed property."""
        product = FinishedProductInventory(
            sku="TEST-001",
            product_name="Test Product",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            quantity=Decimal('100.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A",
            availability_status=AvailabilityStatus.AVAILABLE.value
        )
        
        assert product.is_available is True
        
        # Change to SOLD
        product.availability_status = AvailabilityStatus.SOLD.value
        assert product.is_available is False
        
        # Change to zero quantity
        product.availability_status = AvailabilityStatus.AVAILABLE.value
        product.quantity = Decimal('0.00')
        assert product.is_available is False
    
    def test_is_expiring_soon(self):
        """Test is_expiring_soon property."""
        # Product expiring in 5 days
        product = FinishedProductInventory(
            sku="TEST-002",
            product_name="Test Product",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            quantity=Decimal('50.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A",
            best_before=datetime.utcnow() + timedelta(days=5)
        )
        
        assert product.is_expiring_soon(days=7) is True
        assert product.is_expiring_soon(days=3) is False
        
        # Product with no best_before
        product2 = FinishedProductInventory(
            sku="TEST-003",
            product_name="Test Product 2",
            product_type=ProductType.MERCHANDISE.value,
            category=ProductCategory.MERCH_CAP.value,
            quantity=Decimal('20.00'),
            unit_measure="UNITS",
            cold_room_id="WAREHOUSE",
            best_before=None
        )
        
        assert product2.is_expiring_soon() is False
    
    def test_value_calculation(self):
        """Test inventory value calculation."""
        product = FinishedProductInventory(
            sku="TEST-004",
            product_name="Test Product",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            quantity=Decimal('100.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A",
            unit_cost=Decimal('25.50')
        )
        
        expected_value = Decimal('100.00') * Decimal('25.50')
        assert product.value == expected_value
        
        # Product with no unit cost
        product2 = FinishedProductInventory(
            sku="TEST-005",
            product_name="Test Product 2",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            quantity=Decimal('50.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A"
        )
        
        assert product2.value == Decimal('0.00')
    
    def test_update_quantity_positive(self):
        """Test updating quantity with positive delta."""
        product = FinishedProductInventory(
            sku="TEST-006",
            product_name="Test Product",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            quantity=Decimal('100.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A",
            unit_cost=Decimal('20.00')
        )
        
        product.update_quantity(Decimal('50.00'))
        
        assert product.quantity == Decimal('150.00')
        assert product.total_cost == Decimal('3000.00')
    
    def test_update_quantity_negative(self):
        """Test updating quantity with negative delta."""
        product = FinishedProductInventory(
            sku="TEST-007",
            product_name="Test Product",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            quantity=Decimal('100.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A",
            unit_cost=Decimal('20.00')
        )
        
        product.update_quantity(Decimal('-30.00'))
        
        assert product.quantity == Decimal('70.00')
        assert product.total_cost == Decimal('1400.00')
    
    def test_update_quantity_negative_below_zero_raises(self):
        """Test that updating quantity below zero raises error."""
        product = FinishedProductInventory(
            sku="TEST-008",
            product_name="Test Product",
            product_type=ProductType.OWN_PRODUCTION.value,
            category=ProductCategory.BEER_BOTTLE.value,
            quantity=Decimal('50.00'),
            unit_measure="BOTTLES",
            cold_room_id="COLD_ROOM_A"
        )
        
        with pytest.raises(ValueError) as exc_info:
            product.update_quantity(Decimal('-100.00'))
        
        assert "Cannot reduce quantity below 0" in str(exc_info.value)


class TestColdRoomReading:
    """Tests for ColdRoomReading model."""
    
    def test_check_alert_temperature_high(self):
        """Test alert when temperature is too high."""
        alert_triggered, reason = ColdRoomReading.check_alert_conditions(
            temperature=Decimal('8.5')
        )
        
        assert alert_triggered is True
        assert "too high" in reason.lower()
    
    def test_check_alert_temperature_low(self):
        """Test alert when temperature is too low."""
        alert_triggered, reason = ColdRoomReading.check_alert_conditions(
            temperature=Decimal('-1.0')
        )
        
        assert alert_triggered is True
        assert "too low" in reason.lower()
    
    def test_check_alert_humidity_high(self):
        """Test alert when humidity is too high."""
        alert_triggered, reason = ColdRoomReading.check_alert_conditions(
            temperature=Decimal('4.0'),
            humidity=Decimal('85.0')
        )
        
        assert alert_triggered is True
        assert "humidity" in reason.lower()
    
    def test_check_alert_normal_conditions(self):
        """Test no alert with normal conditions."""
        alert_triggered, reason = ColdRoomReading.check_alert_conditions(
            temperature=Decimal('4.5'),
            humidity=Decimal('65.0')
        )
        
        assert alert_triggered is False
        assert reason is None
    
    def test_create_reading_with_alert(self):
        """Test creating reading that triggers alert."""
        reading = ColdRoomReading.create_reading(
            cold_room_id="COLD_ROOM_A",
            temperature=Decimal('9.0'),
            humidity=Decimal('70.0')
        )
        
        assert reading.cold_room_id == "COLD_ROOM_A"
        assert reading.temperature_celsius == Decimal('9.0')
        assert reading.alert_triggered is True
        assert reading.alert_reason is not None
    
    def test_create_reading_normal(self):
        """Test creating normal reading."""
        reading = ColdRoomReading.create_reading(
            cold_room_id="COLD_ROOM_B",
            temperature=Decimal('4.0')
        )
        
        assert reading.alert_triggered is False
        assert reading.alert_reason is None


class TestProductMovement:
    """Tests for ProductMovement model."""
    
    def test_is_ingress_property(self):
        """Test is_ingress computed property."""
        production_movement = ProductMovement(
            finished_product_id=1,
            movement_type='PRODUCTION',
            quantity=Decimal('100.00')
        )
        assert production_movement.is_ingress is True
        
        sale_movement = ProductMovement(
            finished_product_id=1,
            movement_type='SALE',
            quantity=Decimal('50.00')
        )
        assert sale_movement.is_ingress is False
    
    def test_is_egress_property(self):
        """Test is_egress computed property."""
        sale_movement = ProductMovement(
            finished_product_id=1,
            movement_type='SALE',
            quantity=Decimal('50.00')
        )
        assert sale_movement.is_egress is True
        
        return_movement = ProductMovement(
            finished_product_id=1,
            movement_type='RETURN',
            quantity=Decimal('10.00')
        )
        assert return_movement.is_egress is False
    
    def test_create_from_production(self):
        """Test creating production movement."""
        movement = ProductMovement.create_from_production(
            finished_product_id=5,
            quantity=Decimal('240.00'),
            production_batch_id=42,
            user_id=7
        )
        
        assert movement.movement_type == 'PRODUCTION'
        assert movement.quantity == Decimal('240.00')
        assert movement.user_id == 7
        assert "batch 42" in movement.notes
    
    def test_create_from_sale(self):
        """Test creating sale movement."""
        movement = ProductMovement.create_from_sale(
            finished_product_id=5,
            quantity=Decimal('24.00'),
            sales_order_id=100,
            from_location="COLD_ROOM_A",
            user_id=8
        )
        
        assert movement.movement_type == 'SALE'
        assert movement.quantity == Decimal('24.00')
        assert movement.sales_order_id == 100
        assert movement.from_location == "COLD_ROOM_A"
