"""
Unit tests for Batch State Machine.
"""
import pytest
from models.production_batch import ProductionBatch, BatchStatus
from logic.batch_state_machine import BatchStateMachine


class TestBatchStateMachine:
    """Test batch state transitions."""
    
    def test_valid_transition_planned_to_brewing(self, db_session):
        """Test valid transition: PLANNED → BREWING."""
        batch = ProductionBatch(
            batch_number="TEST-001",
            recipe_id=1,
            recipe_name="Test IPA",
            planned_volume_liters=20.0,
            status=BatchStatus.PLANNED.value
        )
        
        BatchStateMachine.transition(batch, BatchStatus.BREWING)
        
        assert batch.status == BatchStatus.BREWING.value
        assert batch.brewing_started_at is not None
    
    def test_valid_transition_brewing_to_fermenting(self, db_session):
        """Test valid transition: BREWING → FERMENTING."""
        batch = ProductionBatch(
            batch_number="TEST-002",
            recipe_id=1,
            recipe_name="Test IPA",
            planned_volume_liters=20.0,
            status=BatchStatus.BREWING.value
        )
        
        BatchStateMachine.transition(batch, BatchStatus.FERMENTING)
        
        assert batch.status == BatchStatus.FERMENTING.value
        assert batch.fermenting_started_at is not None
    
    def test_valid_transition_to_completed(self, db_session):
        """Test transition to COMPLETED."""
        batch = ProductionBatch(
            batch_number="TEST-003",
            recipe_id=1,
            recipe_name="Test IPA",
            planned_volume_liters=20.0,
            status=BatchStatus.PACKAGING.value
        )
        
        BatchStateMachine.transition(batch, BatchStatus.COMPLETED)
        
        assert batch.status == BatchStatus.COMPLETED.value
        assert batch.completed_at is not None
    
    def test_invalid_transition(self, db_session):
        """Test invalid transition: PLANNED → COMPLETED."""
        batch = ProductionBatch(
            batch_number="TEST-004",
            recipe_id=1,
            recipe_name="Test IPA",
            planned_volume_liters=20.0,
            status=BatchStatus.PLANNED.value
        )
        
        with pytest.raises(ValueError) as exc:
            BatchStateMachine.transition(batch, BatchStatus.COMPLETED)
        
        assert "Invalid transition" in str(exc.value)
    
    def test_cancel_from_any_state(self, db_session):
        """Test cancellation from various states."""
        # Cancel from PLANNED
        batch1 = ProductionBatch(
            batch_number="TEST-005",
            recipe_id=1,
            recipe_name="Test IPA",
            planned_volume_liters=20.0,
            status=BatchStatus.PLANNED.value
        )
        
        BatchStateMachine.transition(batch1, BatchStatus.CANCELLED, notes="Ingredient shortage")
        
        assert batch1.status == BatchStatus.CANCELLED.value
        assert batch1.cancellation_reason == "Ingredient shortage"
    
    def test_skip_conditioning(self, db_session):
        """Test skipping conditioning: FERMENTING → PACKAGING."""
        batch = ProductionBatch(
            batch_number="TEST-006",
            recipe_id=1,
            recipe_name="Test IPA",
            planned_volume_liters=20.0,
            status=BatchStatus.FERMENTING.value
        )
        
        # Should allow FERMENTING → PACKAGING (skip conditioning)
        BatchStateMachine.transition(batch, BatchStatus.PACKAGING)
        
        assert batch.status == BatchStatus.PACKAGING.value
    
    def test_get_next_states(self):
        """Test getting valid next states."""
        next_states = BatchStateMachine.get_next_states(BatchStatus.PLANNED)
        
        assert BatchStatus.BREWING in next_states
        assert BatchStatus.CANCELLED in next_states
        assert len(next_states) == 2
