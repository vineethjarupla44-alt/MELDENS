from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


MANDATORY_DISCLAIMER = (
    "MedLens organizes and explains information contained in the available records. "
    "It does not provide medical diagnosis or treatment recommendations."
)


class ClinicalSummarySections(BaseModel):
    record_overview: str = Field(..., description="Overall summary of the patient profile, records, and active conditions")
    recently_documented: str = Field(..., description="Highlights from the latest clinical reports and encounters")
    laboratory_values: str = Field(..., description="Laboratory test results categorized strictly by source-report status (NORMAL, LOW, HIGH, UNKNOWN)")
    historical_changes: str = Field(..., description="Documented chronological changes or progression across past and present records")
    potential_conflicts: str = Field(..., description="Contradictions, discrepancies, or conflicting documentation across records")
    missing_information: str = Field(..., description="Gaps, missing reference ranges, or omitted clinical details in available records")
    verification_required: str = Field(..., description="Information requiring human clinician verification, low confidence extractions, or unresolved discrepancies")


class SummaryProvenanceSources(BaseModel):
    document_ids: List[str] = Field(default_factory=list, description="IDs of medical documents referenced")
    lab_ids: List[str] = Field(default_factory=list, description="IDs of lab results evaluated")
    medication_ids: List[str] = Field(default_factory=list, description="IDs of medications evaluated")
    condition_ids: List[str] = Field(default_factory=list, description="IDs of conditions referenced")
    allergy_ids: List[str] = Field(default_factory=list, description="IDs of allergies referenced")
    observation_ids: List[str] = Field(default_factory=list, description="IDs of observations/vitals referenced")
    conflict_ids: List[str] = Field(default_factory=list, description="IDs of conflicts noted")


class ClinicalSummaryBase(BaseModel):
    summary_text: str = Field(..., description="Plain-English non-diagnostic translation of documented facts")
    sections: Optional[ClinicalSummarySections] = Field(None, description="The 7 structured clinical summary sections")
    structured_provenance_sources: Optional[SummaryProvenanceSources] = Field(
        None, description="Entity IDs of all structured records utilized in the summary"
    )
    key_findings: Optional[List[str]] = Field(default_factory=list, description="Bullet points of key clinical facts for patient awareness")
    disclaimer: str = Field(
        default=MANDATORY_DISCLAIMER,
        description="Mandatory non-diagnostic medical disclaimer"
    )
    model_version: str = Field(default="medlens-summary-v1", description="Model engine and version used")
    is_ai_generated: bool = Field(default=True, description="Explicit label indicating AI-generated content")
    is_verified: bool = Field(default=False, description="Whether summary has been signed off by a human clinician")


class ClinicalSummaryCreate(ClinicalSummaryBase):
    patient_id: str


class ClinicalSummaryRead(ClinicalSummaryBase):
    id: str
    patient_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClinicalSummaryGenerateRequest(BaseModel):
    force_regenerate: bool = Field(default=False, description="Force re-generation even if a recent summary exists")
