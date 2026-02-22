"""
Custom exceptions for Production Service.
"""


class InsufficientStockError(Exception):
    """
    Raised when not enough inventory to allocate for production.
    
    Attributes:
        ingredient: Name of the ingredient
        required: Required quantity
        available: Available quantity
    """
    
    def __init__(self, ingredient: str, required: float, available: float, unit: str = ""):
        self.ingredient = ingredient
        self.required = required
        self.available = available
        self.unit = unit
        
        unit_str = f" {unit}" if unit else ""
        super().__init__(
            f"Insufficient stock for '{ingredient}': "
            f"required {required}{unit_str}, available {available}{unit_str}"
        )


class ServiceUnavailableError(Exception):
    """Raised when a required service (Inventory, Finance) is unavailable."""
    
    def __init__(self, service_name: str, operation: str):
        self.service_name = service_name
        self.operation = operation
        super().__init__(
            f"{service_name} unavailable during operation: {operation}"
        )


class InvalidBatchStateError(Exception):
    """Raised when batch operation is invalid for current state."""
    
    def __init__(self, batch_id: int, current_state: str, operation: str):
        self.batch_id = batch_id
        self.current_state = current_state
        self.operation = operation
        super().__init__(
            f"Batch #{batch_id} in state '{current_state}' cannot perform: {operation}"
        )
