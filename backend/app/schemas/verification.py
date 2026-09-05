from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VerificationQueueItem(BaseModel):
    id: str
    entity_type: str = Field(..., description="lab, medication, condition, allergy, observation")
    patient_id: str
    patient_name: str
    item_name: str
    extracted_value: str
    original_value: Optional[str] = Field(None, description="Unmodified original AI extraction string")
    editable_value: str = Field(..., description="Initial editable value")
    corrected_value: Optional[str] = Field(None, description="Clinician corrected value if edited")
    source_document: Optional[str] = None
    page_number: Optional[int] = None
    confidence: Optional[float] = None
    reasons: List[str] = Field(default_factory=list, description="Reason flags requiring human review")
    verification_status: str = Field(default="UNVERIFIED")
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    source_snippet: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class VerificationActionRequest(BaseModel):
    entity_type: str
    entity_id: str
    action: str = Field(..., description="ACCEPT, EDIT, or REJECT")
    corrected_value: Optional[str] = Field(None, description="Human corrected value if action is EDIT")
    reviewer_id: str = "CLINICIAN"
    reviewer_name: str = "Dr. Sarah Lin, MD"
    reviewer_role: str = "Clinician Reviewer"
    notes: Optional[str] = None

class VerificationActionResponse(BaseModel):
    status: str
    entity_type: str
    entity_id: str
    action: str
    original_value: Optional[str]
    corrected_value: Optional[str]
    verification_status: str
    verified_by: str
    verified_at: datetime
    audit_id: Optional[str] = None
