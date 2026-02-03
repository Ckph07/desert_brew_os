"""
Unit tests for supplier management.
"""
import pytest
from decimal import Decimal
from models.supplier import Supplier


class TestSupplierModel:
    """Test suite for Supplier model."""
    
    def test_create_supplier(self, db_session):
        """Should create supplier with basic info."""
        supplier = Supplier(
            name="Test Supplier",
            rfc="TST850101ABC",
            email="test@supplier.com",
            phone="+52 81 1234 5678",
            payment_terms="30 días",
            is_active=True
        )
        
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.id is not None
        assert supplier.name == "Test Supplier"
        assert supplier.is_active == True
        assert supplier.preferred == False
    
    def test_supplier_ratings(self, db_session):
        """Should store quality and delivery ratings."""
        supplier = Supplier(
            name="Rated Supplier",
            quality_rating=Decimal("4.5"),
            delivery_rating=Decimal("4.8")
        )
        
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.quality_rating == Decimal("4.5")
        assert supplier.delivery_rating == Decimal("4.8")
    
    def test_supplier_deactivation(self, db_session):
        """Should soft-delete supplier by setting is_active=False."""
        supplier = Supplier(name="Active Supplier", is_active=True)
        db_session.add(supplier)
        db_session.commit()
        
        # Deactivate
        supplier.is_active = False
        db_session.commit()
        
        assert supplier.is_active == False
        assert supplier.id is not None  # Still exists in DB


class TestSupplierStockBatchRelationship:
    """Test relationship between Supplier and StockBatch."""
    
    def test_supplier_has_batches(self, db_session, sample_supplier):
        """StockBatch should reference supplier."""
        from models.stock import StockBatch
        
        supplier = sample_supplier(name="Malterías Tepeyac")
        db_session.add(supplier)
        db_session.flush()
        
        batch = StockBatch(
            sku="MALT-PALE-2ROW",
            category="MALT",
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("100"),
            unit_measure="KG",
            unit_cost=Decimal("18.50"),
            total_cost=Decimal("1850"),
            supplier_id=supplier.id
        )
        
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(supplier)
        
        assert len(supplier.stock_batches) == 1
        assert supplier.stock_batches[0].sku == "MALT-PALE-2ROW"
