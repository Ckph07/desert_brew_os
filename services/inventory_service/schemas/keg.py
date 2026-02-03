"""
Pydantic schemas for Keg Asset management API.
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import datetime
from models.keg_enums import KegState, KegSize, KegType, KegOwnership


class KegAssetCreate(BaseModel):
    """Schema for creating a new keg."""
    serial_number: str = Field(..., max_length=50, description="Unique serial number")
    rfid_tag: Optional[str] = Field(None, max_length=100, description="RFID tag (optional)")
    size_liters: int = Field(..., ge=10, le=100, description="Keg size in liters")
    keg_type: KegType = Field(default=KegType.SANKE_D, description="Keg connection type")
    ownership: KegOwnership = Field(default=KegOwnership.OWN, description="Ownership type")
    guest_brewery_id: Optional[int] = Field(None, description="Guest brewery ID if applicable")
    current_location: Optional[str] = Field(None, max_length=100, description="Initial location")


class KegAssetUpdate(BaseModel):
    """Schema for updating keg attributes (not state)."""
    rfid_tag: Optional[str] = Field(None, max_length=100)
    current_location: Optional[str] = Field(None, max_length=100)
    needs_maintenance: Optional[bool] = None


class KegTransitionRequest(BaseModel):
    """Schema for requesting a state transition."""
    new_state: KegState = Field(..., description="Desired new state")
    user_id: int = Field(..., description="User making the transition")
    location: Optional[str] = Field(None, max_length=100, description="Location")
    reason: Optional[str] = Field(None, max_length=200, description="Reason for transition")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    # Context fields (depending on target state)
    batch_id: Optional[int] = Field(None, description="Batch ID (for FULL state)")
    client_id: Optional[int] = Field(None, description="Client ID (for IN_CLIENT state)")


class KegBulkScanRequest(BaseModel):
    """Schema for bulk RFID scanning."""
    rfid_tags: List[str] = Field(..., min_items=1, description="List of RFID tags")
    new_state: KegState = Field(..., description="Target state for all kegs")
    location: str = Field(..., max_length=100, description="Location")
    user_id: int = Field(..., description="User performing scan")
    notes: Optional[str] = Field(None, max_length=500)


class KegFillBatchRequest(BaseModel):
    """Schema for filling multiple kegs from a batch."""
    batch_id: int = Field(..., description="Production batch ID")
    keg_ids: List[UUID4] = Field(..., min_items=1, description="List of keg IDs to fill")
    filled_by: int = Field(..., description="User ID")
    notes: Optional[str] = Field(None, max_length=500)


class KegTransferRequest(BaseModel):
    """Schema for transferring content between kegs."""
    source_keg_id: UUID4 = Field(..., description="Source keg ID")
    target_keg_ids: List[UUID4] = Field(..., min_items=1, description="Target keg IDs")
    volume_transferred_liters: float = Field(..., gt=0, description="Volume transferred")
    transferred_by: int = Field(..., description="User ID")
    notes: Optional[str] = Field(None, max_length=500)


class KegTransitionResponse(BaseModel):
    """Response schema for a transition."""
    id: int
    keg_id: UUID4
    from_state: str
    to_state: str
    location: Optional[str]
    user_id: Optional[int]
    timestamp: datetime
    bulk_operation_id: Optional[str]
    
    class Config:
        from_attributes = True


class KegAssetResponse(BaseModel):
    """Response schema for keg asset."""
    id: UUID4
    serial_number: str
    rfid_tag: Optional[str]
    size_liters: int
    keg_type: str
    current_state: str
    production_batch_id: Optional[int]
    ownership: str
    guest_brewery_id: Optional[int]
    cycle_count: int
    last_cleaned_at: Optional[datetime]
    last_filled_at: Optional[datetime]
    current_location: Optional[str]
    client_id: Optional[int]
    is_active: bool
    needs_maintenance: bool
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    is_available: bool
    is_filled: bool
    
    class Config:
        from_attributes = True


class KegAssetWithHistory(KegAssetResponse):
    """Keg asset with transition history."""
    transitions: List[KegTransitionResponse] = []


class KegAtRiskResponse(BaseModel):
    """Response for kegs at risk report."""
    keg_id: UUID4
    serial_number: str
    client_id: Optional[int]
    client_name: Optional[str]
    days_out: int
    last_transition_date: datetime
    current_location: Optional[str]


class KegBulkOperationResponse(BaseModel):
    """Response for bulk operations."""
    success_count: int
    failed_count: int
    bulk_operation_id: str
    failed_rfid_tags: List[str] = []
    errors: List[str] = []


class KegTransferResponse(BaseModel):
    """Response for keg transfer."""
    id: int
    source_keg_id: UUID4
    source_batch_id: Optional[int]
    target_keg_ids: List[UUID4]
    volume_transferred_liters: float
    transferred_by: Optional[int]
    transferred_at: datetime
    notes: Optional[str]
    
    class Config:
        from_attributes = True
