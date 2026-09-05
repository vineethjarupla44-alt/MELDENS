from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import enum

class ConflictStatus(str, enum.Enum):
    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class ConflictCategory(str, enum.Enum):
    ALLERGY = "ALLERGY"
    MEDICATION = "MEDICATION"
    LAB_RESULT = "LAB_RESULT"
    DEMOGRAPHIC = "DEMOGRAPHIC"
    OTHER = "OTHER"

class ConflictRecordBase(BaseModel):
    patient_id: str
    category: ConflictCategory
    field_name: str
    
    source_a_type: str
    source_a_document: Optional[str] = None
    source_a_page: Optional[int] = None
    source_a_value: str
    
    source_b_type: str
    source_b_document: Optional[str] = None
    source_b_page: Optional[int] = None
    source_b_value: str
    
    description: str
    severity: str = "MEDIUM" # LOW, MEDIUM, HIGH, CRITICAL
    status: ConflictStatus = Field(default=ConflictStatus.UNRESOLVED)
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None

class ConflictRecordCreate(ConflictRecordBase):
    pass

class ConflictRecordRead(ConflictRecordBase):
    id: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConflictResolveRequest(BaseModel):
    resolution_notes: str = Field(..., description="Clinician notes on how the conflict was resolved")
    resolved_by: str = Field(..., description="Clinician or reviewer username/id")
    status: ConflictStatus = Field(default=ConflictStatus.RESOLVED)
