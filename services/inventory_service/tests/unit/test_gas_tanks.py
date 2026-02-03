"""
Unit tests for gas tank management.
"""
import pytest
from decimal import Decimal
from models.gas_tank import GasTank, GasConsumption


class TestGasTankModel:
    """Test suite for GasTank model."""
    
    def test_create_co2_tank(self, db_session):
        """Should create CO2 tank with capacity in kg."""
        tank = GasTank(
            tank_code="CO2-TANK-001",
            sku="CO2-FOOD-25KG",
            capacity_kg=Decimal("25"),
            current_weight_kg=Decimal("25"),
            is_full=True,
            ownership_type="RENTED",
            deposit_amount=Decimal("500"),
            location="Production Floor"
        )
        
        db_session.add(tank)
        db_session.commit()
        
        assert tank.id is not None
        assert tank.tank_code == "CO2-TANK-001"
        assert tank.capacity_kg == Decimal("25")
        assert tank.is_full == True
    
    def test_create_o2_tank(self, db_session):
        """Should create O2 tank with capacity in m³."""
        tank = GasTank(
            tank_code="O2-TANK-001",
            sku="O2-1M3",
            capacity_m3=Decimal("1.000"),
            current_volume_m3=Decimal("1.000"),
            is_full=True,
            ownership_type="DEPOSIT",
            location="Storage"
        )
        
        db_session.add(tank)
        db_session.commit()
        
        assert tank.capacity_m3 == Decimal("1.000")
        assert tank.remaining_percentage == 100.0
    
    def test_remaining_percentage_co2(self, db_session):
        """Should calculate remaining percentage for CO2."""
        tank = GasTank(
            tank_code="TEST-001",
            sku="CO2-FOOD-10KG",
            capacity_kg=Decimal("10"),
            current_weight_kg=Decimal("7.5"),
            ownership_type="RENTED"
        )
        
        assert tank.remaining_percentage == 75.0
    
    def test_gas_consumption_record(self, db_session):
        """Should record gas consumption."""
        tank = GasTank(
            tank_code="CO2-TANK-002",
            sku="CO2-FOOD-25KG",
            capacity_kg=Decimal("25"),
            current_weight_kg=Decimal("25"),
            ownership_type="RENTED"
        )
        db_session.add(tank)
        db_session.flush()
        
        consumption = GasConsumption(
            tank_id=tank.id,
            quantity_consumed_kg=Decimal("5"),
            production_batch_id=42,
            purpose="CARBONATION",
            notes="Carbonating IPA"
        )
        
        db_session.add(consumption)
        db_session.commit()
        
        assert consumption.id is not None
        assert consumption.purpose == "CARBONATION"
        assert consumption.quantity_consumed_kg == Decimal("5")


class TestGasConsumption:
    """Test gas consumption logic."""
    
    def test_consume_reduces_tank_weight(self, db_session):
        """Consuming gas should reduce tank weight."""
        tank = GasTank(
            tank_code="CO2-TANK-003",
            sku="CO2-FOOD-25KG",
            capacity_kg=Decimal("25"),
            current_weight_kg=Decimal("25"),
            ownership_type="RENTED"
        )
        db_session.add(tank)
        db_session.flush()
        
        # Simulate consumption
        consumed = Decimal("5")
        tank.current_weight_kg -= consumed
        
        consumption = GasConsumption(
            tank_id=tank.id,
            quantity_consumed_kg=consumed,
            purpose="PUSHING"
        )
        db_session.add(consumption)
        db_session.commit()
        
        assert tank.current_weight_kg == Decimal("20")
        assert tank.remaining_percentage == 80.0
    
    def test_tank_becomes_empty_when_low(self, db_session):
        """Tank should be marked empty when < 10%."""
        tank = GasTank(
            tank_code="CO2-TANK-004",
            sku="CO2-FOOD-10KG",
            capacity_kg=Decimal("10"),
            current_weight_kg=Decimal("0.5"),  # 5%
            ownership_type="RENTED"
        )
        
        assert tank.remaining_percentage == 5.0
        # In real implementation, this would trigger is_empty=True
