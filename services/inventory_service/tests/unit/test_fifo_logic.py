"""
Unit tests for FIFO (First-In, First-Out) stock allocation logic.

Critical business logic that must work perfectly.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from logic.stock_rotation import allocate_stock_fifo, InsufficientStockError
from models.stock import StockBatch


class TestFIFOAllocation:
    """Test suite for FIFO stock allocation."""
    
    def test_allocates_from_oldest_batch(self, db_session, sample_stock_batch):
        """
        CRITICAL: FIFO debe consumir del lote más antiguo primero.
        """
        # Arrange: Create 2 batches with different arrival dates
        old_batch = sample_stock_batch(
            sku="MALT-PALE-2ROW",
            quantity=100,
            arrival_date=datetime.utcnow() - timedelta(days=10),
            batch_number="LOT-OLD"
        )
        new_batch = sample_stock_batch(
            sku="MALT-PALE-2ROW",
            quantity=50,
            arrival_date=datetime.utcnow(),
            batch_number="LOT-NEW"
        )
        
        db_session.add(old_batch)
        db_session.add(new_batch)
        db_session.commit()
        
        # Act: Allocate 80kg
        allocations = allocate_stock_fifo(
            sku="MALT-PALE-2ROW",
            amount_needed=Decimal("80"),
            session=db_session
        )
        
        # Assert: Should only use the old batch
        assert len(allocations) == 1
        assert allocations[0]["batch_number"] == "LOT-OLD"
        assert allocations[0]["quantity"] == 80.0
        
        # Verify database state
        db_session.refresh(old_batch)
        db_session.refresh(new_batch)
        assert old_batch.remaining_quantity == Decimal("20")
        assert new_batch.remaining_quantity == Decimal("50")  # Untouched
    
    def test_uses_multiple_batches_when_needed(self, db_session, sample_stock_batch):
        """
        FIFO debe usar múltiples lotes si el primero no es suficiente.
        """
        # Arrange: 3 batches
        batch1 = sample_stock_batch(
            sku="HOPS-CASCADE",
            quantity=50,
            arrival_date=datetime.utcnow() - timedelta(days=5),
            batch_number="LOT-1"
        )
        batch2 = sample_stock_batch(
            sku="HOPS-CASCADE",
            quantity=30,
            arrival_date=datetime.utcnow() - timedelta(days=3),
            batch_number="LOT-2"
        )
        batch3 = sample_stock_batch(
            sku="HOPS-CASCADE",
            quantity=100,
            arrival_date=datetime.utcnow(),
            batch_number="LOT-3"
        )
        
        db_session.add_all([batch1, batch2, batch3])
        db_session.commit()
        
        # Act: Allocate 120g (needs all of batch1, batch2, and part of batch3)
        allocations = allocate_stock_fifo(
            sku="HOPS-CASCADE",
            amount_needed=Decimal("120"),
            session=db_session
        )
        
        # Assert: Used 3 batches
        assert len(allocations) == 3
        assert allocations[0]["batch_number"] == "LOT-1"
        assert allocations[0]["quantity"] == 50.0
        assert allocations[1]["batch_number"] == "LOT-2"
        assert allocations[1]["quantity"] == 30.0
        assert allocations[2]["batch_number"] == "LOT-3"
        assert allocations[2]["quantity"] == 40.0
        
        # Verify remaining quantities
        db_session.refresh(batch1)
        db_session.refresh(batch2)
        db_session.refresh(batch3)
        assert batch1.remaining_quantity == Decimal("0")
        assert batch1.is_allocated == True
        assert batch2.remaining_quantity == Decimal("0")
        assert batch2.is_allocated == True
        assert batch3.remaining_quantity == Decimal("60")
        assert batch3.is_allocated == False
    
    def test_raises_error_on_insufficient_stock(self, db_session, sample_stock_batch):
        """
        Debe fallar con InsufficientStockError si no hay suficiente stock.
        """
        # Arrange: Only 10kg available
        batch = sample_stock_batch(
            sku="YEAST-US05",
            quantity=10,
            batch_number="LOT-SMALL"
        )
        db_session.add(batch)
        db_session.commit()
        
        # Act & Assert: Should raise exception
        with pytest.raises(InsufficientStockError) as exc_info:
            allocate_stock_fifo(
                sku="YEAST-US05",
                amount_needed=Decimal("15"),
                session=db_session
            )
        
        # Verify error details
        error = exc_info.value
        assert error.sku == "YEAST-US05"
        assert error.requested == Decimal("15")
        assert error.available == Decimal("10")
        
        # Database should remain unchanged
        db_session.refresh(batch)
        assert batch.remaining_quantity == Decimal("10")
    
    def test_ignores_different_sku(self, db_session, sample_stock_batch):
        """
        FIFO solo debe considerar lotes del SKU solicitado.
        """
        # Arrange: Different SKUs
        malt_batch = sample_stock_batch(
            sku="MALT-PALE-2ROW",
            quantity=100
        )
        hops_batch = sample_stock_batch(
            sku="HOPS-CASCADE",
            quantity=50
        )
        db_session.add_all([malt_batch, hops_batch])
        db_session.commit()
        
        # Act: Allocate MALT only
        allocations = allocate_stock_fifo(
            sku="MALT-PALE-2ROW",
            amount_needed=Decimal("50"),
            session=db_session
        )
        
        # Assert: Only malt was touched
        assert len(allocations) == 1
        assert allocations[0]["sku"] == "MALT-PALE-2ROW"
        
        db_session.refresh(hops_batch)
        assert hops_batch.remaining_quantity == Decimal("50")  # Untouched
    
    def test_calculates_cost_correctly(self, db_session, sample_stock_batch):
        """
        Debe calcular costos correctamente usando precio de cada lote.
        """
        # Arrange: Batches with different costs
        cheap_batch = sample_stock_batch(
            sku="MALT-MUNICH",
            quantity=100,
            unit_cost=15.00,
            arrival_date=datetime.utcnow() - timedelta(days=2),
            batch_number="CHEAP"
        )
        expensive_batch = sample_stock_batch(
            sku="MALT-MUNICH",
            quantity=100,
            unit_cost=20.00,
            arrival_date=datetime.utcnow(),
            batch_number="EXPENSIVE"
        )
        db_session.add_all([cheap_batch, expensive_batch])
        db_session.commit()
        
        # Act: Allocate 150kg (all cheap + 50kg expensive)
        allocations = allocate_stock_fifo(
            sku="MALT-MUNICH",
            amount_needed=Decimal("150"),
            session=db_session
        )
        
        # Assert: Cost calculation
        assert len(allocations) == 2
        assert allocations[0]["total_cost"] == 100 * 15.00  # 1500.00
        assert allocations[1]["total_cost"] == 50 * 20.00   # 1000.00
        
        # Total cost should be 2500.00
        total_cost = sum(a["total_cost"] for a in allocations)
        assert total_cost == 2500.00
    
    def test_exact_match_allocation(self, db_session, sample_stock_batch):
        """
        Debe manejar correctamente asignaciones exactas.
        """
        # Arrange
        batch = sample_stock_batch(
            sku="LABEL-IPA",
            quantity=1000,
            batch_number="LOT-LABELS"
        )
        db_session.add(batch)
        db_session.commit()
        
        # Act: Allocate exactly all stock
        allocations = allocate_stock_fifo(
            sku="LABEL-IPA",
            amount_needed=Decimal("1000"),
            session=db_session
        )
        
        # Assert
        assert len(allocations) == 1
        assert allocations[0]["quantity"] == 1000.0
        
        db_session.refresh(batch)
        assert batch.remaining_quantity == Decimal("0")
        assert batch.is_allocated == True
