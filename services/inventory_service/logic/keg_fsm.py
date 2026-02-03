"""
Finite State Machine para gestión de estados de barriles.
"""
from typing import Dict, List, Optional
from datetime import datetime
from models.keg_enums import KegState


class InvalidTransitionError(Exception):
    """Raised when an invalid FSM transition is attempted."""
    pass


class ValidationError(Exception):
    """Raised when business rule validation fails."""
    pass


# Transiciones válidas del FSM
VALID_TRANSITIONS: Dict[KegState, List[KegState]] = {
    KegState.EMPTY: [KegState.DIRTY, KegState.CLEAN],
    KegState.DIRTY: [KegState.CLEAN, KegState.QUARANTINE],
    KegState.CLEAN: [KegState.FILLING, KegState.DIRTY],
    KegState.FILLING: [KegState.FULL, KegState.CLEAN],  # Si falla el llenado
    KegState.FULL: [KegState.TAPPED, KegState.IN_TRANSIT, KegState.IN_CLIENT],
    KegState.TAPPED: [KegState.EMPTY],
    KegState.IN_CLIENT: [KegState.IN_TRANSIT],
    KegState.IN_TRANSIT: [KegState.EMPTY, KegState.IN_CLIENT],
    KegState.QUARANTINE: [KegState.CLEAN, KegState.RETIRED],
    KegState.RETIRED: []  # Terminal state
}


class KegStateMachine:
    """
    Finite State Machine para barriles con validaciones.
    
    Valida transiciones y aplica reglas de negocio.
    """
    
    @staticmethod
    def can_transition(from_state: KegState, to_state: KegState) -> bool:
        """
        Check if transition is valid according to FSM.
        
        Args:
            from_state: Current state
            to_state: Desired state
            
        Returns:
            True if transition is valid
        """
        valid_targets = VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_targets
    
    @staticmethod
    def validate_transition(
        keg,
        new_state: KegState,
        context: Optional[Dict] = None
    ) -> None:
        """
        Validate transition and raise if invalid.
        
        Args:
            keg: KegAsset instance
            new_state: Desired new state
            context: Additional context (batch_id, client_id, etc.)
            
        Raises:
            InvalidTransitionError: If FSM transition is invalid
            ValidationError: If business rules are violated
        """
        context = context or {}
        current_state = KegState(keg.current_state)
        
        # Check 1: Valid FSM transition
        if not KegStateMachine.can_transition(current_state, new_state):
            raise InvalidTransitionError(
                f"Cannot transition from {current_state.value} to {new_state.value}. "
                f"Valid transitions: {[s.value for s in VALID_TRANSITIONS.get(current_state, [])]}"
            )
        
        # Check 2: Business rule validations
        
        # Rule: Only fill CLEAN kegs
        if new_state == KegState.FILLING:
            if current_state != KegState.CLEAN:
                raise ValidationError("Can only fill CLEAN kegs. Current state: {current_state.value}")
        
        # Rule: Must have batch_id when filling
        if new_state == KegState.FULL:
            if not context.get("batch_id"):
                raise ValidationError("batch_id required when marking keg as FULL")
        
        # Rule: Must have client_id for IN_CLIENT
        if new_state == KegState.IN_CLIENT:
            if not context.get("client_id"):
                raise ValidationError("client_id required for IN_CLIENT state")
        
        # Rule: Cannot retire keg if it has beer
        if new_state == KegState.RETIRED:
            if keg.production_batch_id:
                raise ValidationError(
                    f"Cannot retire keg with beer. Empty it first. "
                    f"Current batch: {keg.production_batch_id}"
                )
    
    @staticmethod
    def apply_state_changes(keg, new_state: KegState, context: Optional[Dict] = None) -> None:
        """
        Apply state-specific changes to keg.
        
        Args:
            keg: KegAsset instance
            new_state: New state being applied
            context: Additional context
        """
        context = context or {}
        
        # Update state
        keg.current_state = new_state.value
        keg.updated_at = datetime.utcnow()
        
        # State-specific updates
        if new_state == KegState.CLEAN:
            keg.last_cleaned_at = datetime.utcnow()
            keg.production_batch_id = None  # Clear batch
            
        elif new_state == KegState.FULL:
            keg.last_filled_at = datetime.utcnow()
            keg.production_batch_id = context.get("batch_id")
            keg.cycle_count += 1
            
        elif new_state == KegState.IN_CLIENT:
            keg.client_id = context.get("client_id")
            keg.current_location = context.get("location", "Cliente")
            
        elif new_state == KegState.EMPTY:
            keg.production_batch_id = None
            keg.client_id = None
            
        elif new_state == KegState.RETIRED:
            keg.is_active = False
    
    @staticmethod
    def get_valid_next_states(current_state: KegState) -> List[KegState]:
        """
        Get list of valid next states from current state.
        
        Args:
            current_state: Current keg state
            
        Returns:
            List of valid next states
        """
        return VALID_TRANSITIONS.get(current_state, [])
