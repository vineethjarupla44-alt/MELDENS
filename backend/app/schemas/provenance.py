from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import enum

class ProvenanceSource(str, enum.Enum):
    PATIENT_INPUT = "PATIENT_INPUT"
    DOCUMENT_EXTRACTION = "DOCUMENT_EXTRACTION"
    AI_GENERATED = "AI_GENERATED"
    HUMAN_VERIFIED = "HUMAN_VERIFIED"

class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"

class ProvenanceMetadata(BaseModel):
    source_type: ProvenanceSource = Field(default=ProvenanceSource.DOCUMENT_EXTRACTION, description="Origin source of the data")
    source_document: Optional[str] = Field(None, description="Original source document filename")
    source_page: Optional[int] = Field(None, description="Page number where the entity was identified")
    confidence: Optional[float] = Field(None, description="Extraction confidence score from 0.0 to 1.0")
    source_snippet: Optional[str] = Field(None, description="Exact text quotation from source document")
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED, description="Human review status")
    verified_by: Optional[str] = Field(None, description="Identifier of the verifying clinician/user")
    verified_at: Optional[datetime] = Field(None, description="Timestamp of human verification")

    class Config:
        from_attributes = True

class ProvenanceRecordBase(BaseModel):
    entity_type: str
    entity_id: str
    source_type: ProvenanceSource
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    page_number: Optional[int] = None
    extraction_confidence: Optional[float] = None
    raw_extracted_text: Optional[str] = None
    extraction_method: str = "PDF_PARSER"

class ProvenanceRecordCreate(ProvenanceRecordBase):
    pass

class ProvenanceRecordRead(ProvenanceRecordBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class VerificationRecordCreate(BaseModel):
    entity_type: str
    entity_id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_role: str = "Clinician Reviewer"
    status: VerificationStatus
    notes: Optional[str] = None

class VerificationRecordRead(VerificationRecordCreate):
    id: str
    signed_at: datetime

    class Config:
        from_attributes = True

class ClinicalProvenanceDetail(BaseModel):
    entity_type: str = Field(..., description="lab, medication, condition, allergy, observation")
    entity_id: str
    item_name: str = Field(..., description="Human readable item label, e.g. Hemoglobin")
    item_value: Optional[str] = Field(None, description="Formatted value with unit, e.g. 11.2 g/dL")
    raw_value: Optional[str] = Field(None, description="Unmodified original raw text from source")
    source_type: ProvenanceSource = Field(..., description="PATIENT_INPUT, DOCUMENT_EXTRACTION, AI_GENERATED, HUMAN_VERIFIED")
    method: str = Field(default="AI Extraction", description="Human-readable extraction/input method")
    document_id: Optional[str] = None
    filename: Optional[str] = Field(None, description="Source document filename")
    page_number: Optional[int] = Field(None, description="Page number in document")
    extraction_timestamp: Optional[datetime] = Field(None, description="Timestamp of extraction or entry")
    confidence: Optional[float] = Field(None, description="Confidence score from 0.0 to 1.0")
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    source_snippet: Optional[str] = Field(None, description="Verbatim text quotation from source document")
    document_stream_url: Optional[str] = None

