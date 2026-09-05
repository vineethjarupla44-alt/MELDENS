from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.clinical import LabResultRead, MedicationRead, ConditionRead, AllergyRead, ObservationRead
from app.schemas.document import DocumentRead

class PatientProfileBase(BaseModel):
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    preferred_language: str = "English"
    insurance_provider: Optional[str] = None
    baseline_notes: Optional[str] = None
    symptoms: Optional[str] = None

class PatientProfileCreate(PatientProfileBase):
    patient_id: str

class PatientProfileRead(PatientProfileBase):
    id: str
    patient_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientBase(BaseModel):
    mrn: Optional[str] = Field(None, description="Medical Record Number")
    first_name: str = Field(..., description="First Name")
    last_name: str = Field(..., description="Last Name")
    date_of_birth: Optional[str] = Field(None, description="YYYY-MM-DD")
    gender: Optional[str] = Field(None, description="Biological sex / gender")
    blood_type: Optional[str] = Field(None, description="Blood type ABO/Rh")

class PatientCreate(PatientBase):
    profile: Optional[PatientProfileBase] = None

class PatientRead(PatientBase):
    id: str
    created_at: datetime
    updated_at: datetime
    profile: Optional[PatientProfileRead] = None

    class Config:
        from_attributes = True

class PatientDetail(PatientRead):
    documents: List[DocumentRead] = []
    lab_results: List[LabResultRead] = []
    medications: List[MedicationRead] = []
    conditions: List[ConditionRead] = []
    allergies: List[AllergyRead] = []
    observations: List[ObservationRead] = []

    class Config:
        from_attributes = True
