from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TimelineEventBase(BaseModel):
    event_date: str = Field(..., description="Date of the clinical event (YYYY-MM-DD)")
    event_type: str = Field(..., description="LAB_TEST, MEDICATION_ACTIVE, CONDITION_ONSET, VITAL_SIGN, ENCOUNTER")
    title: str = Field(..., description="Brief summary title")
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    importance: str = Field(default="ROUTINE", description="ROUTINE, SIGNIFICANT, CRITICAL")

class TimelineEventCreate(TimelineEventBase):
    patient_id: str

class TimelineEventRead(TimelineEventBase):
    id: str
    patient_id: str
    created_at: datetime

    class Config:
        from_attributes = True
