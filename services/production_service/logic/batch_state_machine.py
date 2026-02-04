"""
Batch State Machine - Manage ProductionBatch state transitions.

Enforces valid state transitions and updates timestamps.
"""
from models.production_batch import ProductionBatch, BatchStatus
from datetime import datetime
from typing import Dict, List


class BatchStateMachine:
    """
    State machine for ProductionBatch lifecycle.
    
    Valid transitions:
    PLANNED → BREWING → FERMENTING → CONDITIONING → PACKAGING → COMPLETED
                ↓                        ↓
            CANCELLED               PACKAGING (skip conditioning)
    """
    
    VALID_TRANSITIONS: Dict[BatchStatus, List[BatchStatus]] = {
        BatchStatus.PLANNED: [BatchStatus.BREWING, BatchStatus.CANCELLED],
        BatchStatus.BREWING: [BatchStatus.FERMENTING, BatchStatus.CANCELLED],
        BatchStatus.FERMENTING: [BatchStatus.CONDITIONING, BatchStatus.PACKAGING, BatchStatus.CANCELLED],
        BatchStatus.CONDITIONING: [BatchStatus.PACKAGING, BatchStatus.CANCELLED],
        BatchStatus.PACKAGING: [BatchStatus.COMPLETED, BatchStatus.CANCELLED],
        BatchStatus.COMPLETED: [],  # Terminal state
        BatchStatus.CANCELLED: [],  # Terminal state
    }
    
    @staticmethod
    def can_transition(current_status: BatchStatus, new_status: BatchStatus) -> bool:
        """Check if transition is valid."""
        return new_status in BatchStateMachine.VALID_TRANSITIONS.get(current_status, [])
    
    @staticmethod
    def transition(batch: ProductionBatch, new_status: BatchStatus, notes: str = None) -> None:
        """
        Transition batch to new status.
        
        Args:
            batch: ProductionBatch to transition
            new_status: Target status
            notes: Optional notes about transition
            
        Raises:
            ValueError: If transition is invalid
        """
        current_status_enum = BatchStatus(batch.status)
        
        if not BatchStateMachine.can_transition(current_status_enum, new_status):
            valid_transitions = BatchStateMachine.VALID_TRANSITIONS.get(current_status_enum, [])
            raise ValueError(
                f"Invalid transition: {batch.status} → {new_status.value}. "
                f"Valid transitions: {[s.value for s in valid_transitions]}"
            )
        
        # Update status
        batch.status = new_status.value
        
        # Update timestamp based on new status
        now = datetime.utcnow()
        
        if new_status == BatchStatus.BREWING:
            batch.brewing_started_at = now
        elif new_status == BatchStatus.FERMENTING:
            batch.fermenting_started_at = now
        elif new_status == BatchStatus.CONDITIONING:
            batch.conditioning_started_at = now
        elif new_status == BatchStatus.PACKAGING:
            batch.packaging_started_at = now
        elif new_status == BatchStatus.COMPLETED:
            batch.completed_at = now
        elif new_status == BatchStatus.CANCELLED:
            batch.cancelled_at = now
            if notes:
                batch.cancellation_reason = notes
        
        # Update notes if provided
        if notes and new_status != BatchStatus.CANCELLED:
            if batch.notes:
                batch.notes += f"\n[{now.isoformat()}] {batch.status}: {notes}"
            else:
                batch.notes = f"[{now.isoformat()}] {batch.status}: {notes}"
    
    @staticmethod
    def get_next_states(current_status: BatchStatus) -> List[BatchStatus]:
        """Get list of valid next states for current status."""
        return BatchStateMachine.VALID_TRANSITIONS.get(current_status, [])
