"""
Unit tests for stock transfer functionality.

Tests the transfer_stock() function and movement logging.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from logic.stock_rotation import transfer_stock, log_movement, InsufficientStockError
from models.stock import StockBatch
from models.movement import StockMovement
from models.transfer import StockTransfer
from models.enums import MovementType, MovementOrigin, TransferStatus


class TestStockTransfers:
    """Test suite for stock transfer functionality."""
    
    def test_transfer_creates_new_batch_at_destination(self, db_session, sample_stock_batch):
        """Transfer should create new batch at destination."""
        # Arrange: Create stock at Silo A
        batch = sample_stock_batch(
            sku="MALT-PALE-2ROW",
            quantity=100,
            batch_number="LOT-SOURCE"
        )
        batch.location = "Silo A"
        db_session.add(batch)
        db_session.commit()
        
        # Act: Transfer 50kg to Silo B
        transfer = transfer_stock(
            sku="MALT-PALE-2ROW",
            quantity=Decimal("50"),
            from_location="Silo A",
            to_location="Silo B",
            requested_by="test_user",
            session=db_session
        )
        
        # Assert: Transfer created
        assert transfer.id is not None
        assert transfer.status == TransferStatus.COMPLETED.value
        assert transfer.sku == "MALT-PALE-2ROW"
        assert transfer.quantity == Decimal("50")
        
        # Verify source batch deducted
        db_session.refresh(batch)
        assert batch.remaining_quantity == Decimal("50")
        
        # Verify new batch created at destination
        dest_batches = db_session.query(StockBatch).filter(
            StockBatch.location == "Silo B",
            StockBatch.sku == "MALT-PALE-2ROW"
        ).all()
        assert len(dest_batches) == 1
        assert dest_batches[0].remaining_quantity == Decimal("50")
    
    def test_transfer_uses_fifo_from_multiple_batches(self, db_session, sample_stock_batch):
        """Transfer should use FIFO if multiple source batches exist."""
        # Arrange: 2 batches at Silo A
        old_batch = sample_stock_batch(
            sku="HOPS-CASCADE",
            quantity=30,
            arrival_date=datetime.utcnow() - timedelta(days=10),
            batch_number="OLD"
        )
        old_batch.location = "Silo A"
        
        new_batch = sample_stock_batch(
            sku="HOPS-CASCADE",
            quantity=50,
            arrival_date=datetime.utcnow(),
            batch_number="NEW"
        )
        new_batch.location = "Silo A"
        
        db_session.add_all([old_batch, new_batch])
        db_session.commit()
        
        # Act: Transfer 60g (needs both batches)
        transfer = transfer_stock(
            sku="HOPS-CASCADE",
            quantity=Decimal("60"),
            from_location="Silo A",
            to_location="Cold Storage",
            session=db_session
        )
        
        # Assert: Both source batches used (FIFO)
        db_session.refresh(old_batch)
        db_session.refresh(new_batch)
        assert old_batch.remaining_quantity == Decimal("0")
        assert new_batch.remaining_quantity == Decimal("20")  # 50 - 30 = 20
        
        # 2 new batches created at destination
        dest_batches = db_session.query(StockBatch).filter(
            StockBatch.location == "Cold Storage",
            StockBatch.sku == "HOPS-CASCADE"
        ).all()
        assert len(dest_batches) == 2
        total_dest = sum(b.remaining_quantity for b in dest_batches)
        assert total_dest == Decimal("60")
    
    def test_transfer_fails_if_insufficient_stock_at_location(self, db_session, sample_stock_batch):
        """Transfer should fail if source location has insufficient stock."""
        # Arrange: Only 10kg at Silo A
        batch = sample_stock_batch(
            sku="MALT-MUNICH",
            quantity=10,
            batch_number="SMALL"
        )
        batch.location = "Silo A"
        db_session.add(batch)
        db_session.commit()
        
        # Act & Assert: Should fail
        with pytest.raises(InsufficientStockError) as exc_info:
            transfer_stock(
                sku="MALT-MUNICH",
                quantity=Decimal("20"),
                from_location="Silo A",
                to_location="Silo B",
                session=db_session
            )
        
        error = exc_info.value
        assert error.requested == Decimal("20")
        assert error.available == Decimal("10")
    
    def test_transfer_ignores_stock_at_other_locations(self, db_session, sample_stock_batch):
        """Transfer should only consider stock at source location."""
        # Arrange: Stock at different locations
        silo_a = sample_stock_batch(sku="MALT-PALE-2ROW", quantity=50)
        silo_a.location = "Silo A"
        
        silo_b = sample_stock_batch(sku="MALT-PALE-2ROW", quantity=100)
        silo_b.location = "Silo B"
        
        db_session.add_all([silo_a, silo_b])
        db_session.commit()
        
        # Act & Assert: Transfer from Silo A should fail (only 50kg there)
        with pytest.raises(InsufficientStockError):
            transfer_stock(
                sku="MALT-PALE-2ROW",
                quantity=Decimal("80"),
                from_location="Silo A",  # Only 50kg here
                to_location="Cold Storage",
                session=db_session
            )


class TestMovementLogging:
    """Test suite for movement audit trail."""
    
    def test_log_movement_creates_audit_record(self, db_session):
        """log_movement should create audit trail record."""
        # Act: Log a movement
        movement = log_movement(
            session=db_session,
            batch_id=123,
            sku="MALT-PALE-2ROW",
            movement_type=MovementType.CONSUMPTION,
            quantity=Decimal("50"),
            unit_measure="KG",
            movement_origin=MovementOrigin.PRODUCTION,
            reference="Production Order #42",
            created_by="brewer1",
            unit_cost=Decimal("18.50")
        )
        db_session.commit()
        
        # Assert
        assert movement.id is not None
        assert movement.sku == "MALT-PALE-2ROW"
        assert movement.movement_type == MovementType.CONSUMPTION.value
        assert movement.quantity == Decimal("50")
        assert movement.reference == "Production Order #42"
        assert movement.created_by == "brewer1"
        assert movement.total_cost == Decimal("925.00")  # 50 * 18.50
    
    def test_movements_logged_during_transfer(self, db_session, sample_stock_batch):
        """Transfers should log movements for audit trail."""
        # Arrange
        batch = sample_stock_batch(sku="HOPS-SIMCOE", quantity=100)
        batch.location = "Warehouse"
        db_session.add(batch)
        db_session.commit()
        
        # Act: Transfer
        transfer_stock(
            sku="HOPS-SIMCOE",
            quantity=Decimal("30"),
            from_location="Warehouse",
            to_location="Taproom",
            requested_by="manager1",
            session=db_session
        )
        
        # Assert: Movements logged
        movements = db_session.query(StockMovement).filter(
            StockMovement.sku == "HOPS-SIMCOE"
        ).all()
        
        # Should have 2 movements: consumption from source + transfer to dest
        assert len(movements) == 2
        
        # Check consumption movement
        consumption = [m for m in movements if m.movement_type == MovementType.CONSUMPTION.value][0]
        assert consumption.from_location == "Warehouse"
        assert consumption.quantity == Decimal("30")
        
        # Check transfer movement
        transfer_mov = [m for m in movements if m.movement_type == MovementType.TRANSFER.value][0]
        assert transfer_mov.to_location == "Taproom"
        assert transfer_mov.quantity == Decimal("30")
