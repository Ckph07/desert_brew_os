"""
Unit tests for KegStateMachine.
"""
import pytest
from models.keg_enums import KegState
from models.keg_asset import KegAsset
from logic.keg_fsm import KegStateMachine, InvalidTransitionError, ValidationError
import uuid


class TestKegStateMachine:
    """Tests for FSM logic and validations."""
    
    def test_valid_transition_empty_to_dirty(self):
        """Test valid transition: EMPTY → DIRTY."""
        assert KegStateMachine.can_transition(KegState.EMPTY, KegState.DIRTY) is True
    
    def test_valid_transition_dirty_to_clean(self):
        """Test valid transition: DIRTY → CLEAN."""
        assert KegStateMachine.can_transition(KegState.DIRTY, KegState.CLEAN) is True
    
    def test_valid_transition_clean_to_filling(self):
        """Test valid transition: CLEAN → FILLING."""
        assert KegStateMachine.can_transition(KegState.CLEAN, KegState.FILLING) is True
    
    def test_valid_transition_full_to_tapped(self):
        """Test valid transition: FULL → TAPPED."""
        assert KegStateMachine.can_transition(KegState.FULL, KegState.TAPPED) is True
    
    def test_invalid_transition_empty_to_full(self):
        """Test invalid transition: EMPTY → FULL (skip cleaning)."""
        assert KegStateMachine.can_transition(KegState.EMPTY, KegState.FULL) is False
    
    def test_invalid_transition_dirty_to_filling(self):
        """Test invalid transition: DIRTY → FILLING (must clean first)."""
        assert KegStateMachine.can_transition(KegState.DIRTY, KegState.FILLING) is False
    
    def test_invalid_transition_from_retired(self):
        """Test terminal state: RETIRED has no valid transitions."""
        assert KegStateMachine.can_transition(KegState.RETIRED, KegState.CLEAN) is False
        assert len(KegStateMachine.get_valid_next_states(KegState.RETIRED)) == 0
    
    def test_validate_transition_dirty_to_filling_raises(self):
        """Test validation raises error for invalid transition."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-001",
            size_liters=30,
            current_state=KegState.DIRTY.value
        )
        
        with pytest.raises(InvalidTransitionError) as exc_info:
            KegStateMachine.validate_transition(keg, KegState.FILLING)
        
        assert "Cannot transition" in str(exc_info.value)
    
    def test_validate_transition_filling_without_clean_raises(self):
        """Test FILLING requires CLEAN state."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-002",
            size_liters=30,
            current_state=KegState.EMPTY.value
        )
        
        # EMPTY → FILLING is not valid (must go through CLEAN)
        with pytest.raises(InvalidTransitionError):
            KegStateMachine.validate_transition(keg, KegState.FILLING)
    
    def test_validate_transition_full_requires_batch_id(self):
        """Test FULL state requires batch_id in context."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-003",
            size_liters=30,
            current_state=KegState.FILLING.value
        )
        
        # Missing batch_id
        with pytest.raises(ValidationError) as exc_info:
            KegStateMachine.validate_transition(keg, KegState.FULL, context={})
        
        assert "batch_id required" in str(exc_info.value)
    
    def test_validate_transition_in_client_requires_client_id(self):
        """Test IN_CLIENT state requires client_id in context."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-004",
            size_liters=30,
            current_state=KegState.FULL.value
        )
        
        # Missing client_id
        with pytest.raises(ValidationError) as exc_info:
            KegStateMachine.validate_transition(keg, KegState.IN_CLIENT, context={})
        
        assert "client_id required" in str(exc_info.value)
    
    def test_apply_state_changes_clean_clears_batch(self):
        """Test CLEAN state clears batch_id."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-005",
            size_liters=30,
            current_state=KegState.DIRTY.value,
            production_batch_id=42
        )
        
        KegStateMachine.apply_state_changes(keg, KegState.CLEAN)
        
        assert keg.current_state == KegState.CLEAN.value
        assert keg.production_batch_id is None
        assert keg.last_cleaned_at is not None
    
    def test_apply_state_changes_full_sets_batch(self):
        """Test FULL state sets batch_id and increments cycle."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-006",
            size_liters=30,
            current_state=KegState.FILLING.value,
            cycle_count=5
        )
        
        KegStateMachine.apply_state_changes(
            keg, 
            KegState.FULL,
            context={"batch_id": 42}
        )
        
        assert keg.current_state == KegState.FULL.value
        assert keg.production_batch_id == 42
        assert keg.cycle_count == 6
        assert keg.last_filled_at is not None
    
    def test_apply_state_changes_in_client_sets_location(self):
        """Test IN_CLIENT state sets client_id and location."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-007",
            size_liters=30,
            current_state=KegState.FULL.value
        )
        
        KegStateMachine.apply_state_changes(
            keg,
            KegState.IN_CLIENT,
            context={"client_id": 25, "location": "Restaurante El Túnel"}
        )
        
        assert keg.current_state == KegState.IN_CLIENT.value
        assert keg.client_id == 25
        assert keg.current_location == "Restaurante El Túnel"
    
    def test_apply_state_changes_empty_clears_batch_and_client(self):
        """Test EMPTY state clears batch and client."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-008",
            size_liters=30,
            current_state=KegState.TAPPED.value,
            production_batch_id=42,
            client_id=25
        )
        
        KegStateMachine.apply_state_changes(keg, KegState.EMPTY)
        
        assert keg.current_state == KegState.EMPTY.value
        assert keg.production_batch_id is None
        assert keg.client_id is None
    
    def test_apply_state_changes_retired_deactivates_keg(self):
        """Test RETIRED state deactivates keg."""
        keg = KegAsset(
            id=uuid.uuid4(),
            serial_number="TEST-009",
            size_liters=30,
            current_state=KegState.QUARANTINE.value,
            is_active=True
        )
        
        KegStateMachine.apply_state_changes(keg, KegState.RETIRED)
        
        assert keg.current_state == KegState.RETIRED.value
        assert keg.is_active is False
    
    def test_get_valid_next_states(self):
        """Test getting valid next states from current state."""
        # EMPTY can go to DIRTY or CLEAN
        valid_states = KegStateMachine.get_valid_next_states(KegState.EMPTY)
        assert KegState.DIRTY in valid_states
        assert KegState.CLEAN in valid_states
        assert len(valid_states) == 2
        
        # FULL can go to TAPPED, IN_TRANSIT, or IN_CLIENT
        valid_states = KegStateMachine.get_valid_next_states(KegState.FULL)
        assert KegState.TAPPED in valid_states
        assert KegState.IN_TRANSIT in valid_states
        assert KegState.IN_CLIENT in valid_states
        assert len(valid_states) == 3
