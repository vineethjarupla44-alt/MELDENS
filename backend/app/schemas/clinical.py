from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import enum
from app.schemas.provenance import ProvenanceSource, VerificationStatus

class LabStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"

# --- Lab Results ---
class LabResultBase(BaseModel):
    test_name: str = Field(..., description="Name of laboratory test (e.g., Hemoglobin, Fasting Glucose)")
    raw_value: Optional[str] = Field(None, description="Original verbatim text extracted from report (e.g. 11.2, <0.05, Negative)")
    value: Optional[float] = Field(None, description="Parsed numeric result value if applicable")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g. g/dL, mg/dL)")

    # Strict report-derived bounds; NULL allowed, NEVER auto-populated
    reference_range_low: Optional[float] = Field(None, description="Parsed lower bound from report. NULL if not provided.")
    reference_range_high: Optional[float] = Field(None, description="Parsed upper bound from report. NULL if not provided.")
    reference_range_text: Optional[str] = Field(None, description="Verbatim reference range text from report. NULL if not provided.")
    status: LabStatus = Field(default=LabStatus.UNKNOWN, description="NORMAL, LOW, HIGH, or UNKNOWN strictly from report range")
    report_date: Optional[str] = Field(None, description="Date of collection/result from document")

    # Provenance
    provenance_source: ProvenanceSource = Field(default=ProvenanceSource.DOCUMENT_EXTRACTION)
    source_document: Optional[str] = Field(None, description="Document filename/origin")
    source_page: Optional[int] = Field(None, description="Page number in document")
    confidence: Optional[float] = Field(None, description="Extraction confidence (0.0 - 1.0)")
    source_snippet: Optional[str] = Field(None, description="Quoted snippet from document")
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

class LabResultCreate(LabResultBase):
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None

class LabResultRead(LabResultBase):
    id: str
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Medications ---
class MedicationBase(BaseModel):
    medication_name: str = Field(..., description="Brand or generic medication name")
    dosage: Optional[str] = Field(None, description="Dosage amount and unit (e.g. 500 mg)")
    frequency: Optional[str] = Field(None, description="Dosing schedule (e.g. Once daily, BID)")
    route: Optional[str] = Field(None, description="Administration route (e.g. Oral, IV)")
    clinical_status: str = Field(default="ACTIVE", description="ACTIVE, DISCONTINUED, or UNKNOWN")
    prescribed_date: Optional[str] = None
    raw_text: Optional[str] = Field(None, description="Verbatim extracted prescription text")

    # Provenance
    provenance_source: ProvenanceSource = Field(default=ProvenanceSource.DOCUMENT_EXTRACTION)
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    confidence: Optional[float] = None
    source_snippet: Optional[str] = None
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

class MedicationCreate(MedicationBase):
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None

class MedicationRead(MedicationBase):
    id: str
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Conditions ---
class ConditionBase(BaseModel):
    condition_name: str = Field(..., description="Documented condition or finding name")
    icd10_code: Optional[str] = Field(None, description="Documented ICD-10 code if explicitly present")
    onset_date: Optional[str] = None
    clinical_status: str = Field(default="ACTIVE", description="ACTIVE, RESOLVED, or UNKNOWN")
    raw_text: Optional[str] = None

    # Provenance
    provenance_source: ProvenanceSource = Field(default=ProvenanceSource.DOCUMENT_EXTRACTION)
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    confidence: Optional[float] = None
    source_snippet: Optional[str] = None
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

class ConditionCreate(ConditionBase):
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None

class ConditionRead(ConditionBase):
    id: str
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Allergies ---
class AllergyBase(BaseModel):
    allergen: str = Field(..., description="Documented allergen (e.g. Penicillin, Sulfa)")
    reaction: Optional[str] = Field(None, description="Reported allergic reaction (e.g. Anaphylaxis, Rash)")
    severity: Optional[str] = Field(None, description="MILD, MODERATE, SEVERE, or UNKNOWN")
    raw_text: Optional[str] = None

    # Provenance
    provenance_source: ProvenanceSource = Field(default=ProvenanceSource.DOCUMENT_EXTRACTION)
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    confidence: Optional[float] = None
    source_snippet: Optional[str] = None
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

class AllergyCreate(AllergyBase):
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None

class AllergyRead(AllergyBase):
    id: str
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Observations (Vitals / Findings) ---
class ObservationBase(BaseModel):
    observation_type: str = Field(..., description="BLOOD_PRESSURE, HEART_RATE, SPO2, BMI, etc.")
    observation_name: str = Field(..., description="Human readable label, e.g. Blood Pressure")
    numeric_value: Optional[float] = None
    string_value: Optional[str] = None
    unit: Optional[str] = None
    observation_date: Optional[str] = None

    # Provenance
    provenance_source: ProvenanceSource = Field(default=ProvenanceSource.DOCUMENT_EXTRACTION)
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    confidence: Optional[float] = None
    source_snippet: Optional[str] = None
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

class ObservationCreate(ObservationBase):
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None

class ObservationRead(ObservationBase):
    id: str
    patient_id: str
    document_id: Optional[str] = None
    page_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
