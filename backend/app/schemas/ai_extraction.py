from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import enum

class ExtractionConfidenceLevel(str, enum.Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNCERTAIN = "UNCERTAIN"

class ExtractedLabItem(BaseModel):
    test_name: str = Field(..., description="Standardized verbatim name of laboratory test")
    raw_value: Optional[str] = Field(None, description="Original verbatim text of the value from the report")
    value: Optional[float] = Field(None, description="Parsed numeric value if measurable")
    unit: Optional[str] = Field(None, description="Unit of measurement exactly as specified in the report")
    
    # Strictly report-derived bounds; NULL allowed, NEVER invented
    reference_range_low: Optional[float] = Field(None, description="Lower reference bound from report. NULL if not stated.")
    reference_range_high: Optional[float] = Field(None, description="Upper reference bound from report. NULL if not stated.")
    reference_range_text: Optional[str] = Field(None, description="Verbatim text of reference interval from report. NULL if not stated.")
    
    observation: Optional[str] = Field(None, description="Clinical observation note verbatim from report (e.g. Lipemic, Hemolyzed, Flagged)")
    report_date: Optional[str] = Field(None, description="Date of specimen collection or report if explicitly documented")
    source_page: int = Field(..., ge=1, description="1-indexed source document page number")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction certainty score between 0.0 and 1.0")
    source_snippet: Optional[str] = Field(None, description="Exact text excerpt supporting this extraction")
    requires_human_verification: bool = Field(default=False, description="Flagged true if confidence < 0.85 or values are ambiguous")

    @field_validator("confidence")
    @classmethod
    def check_confidence_bounds(cls, v: float) -> float:
        return max(0.0, min(1.0, round(v, 3)))

class ExtractedMedicationItem(BaseModel):
    medication_name: str = Field(..., description="Documented medication brand or generic name")
    dosage: Optional[str] = Field(None, description="Dosage strength and amount verbatim from report")
    frequency: Optional[str] = Field(None, description="Documented administration frequency (e.g. daily, BID)")
    route: Optional[str] = Field(None, description="Route of administration (e.g. oral, topical)")
    source_page: int = Field(..., ge=1)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    source_snippet: Optional[str] = None
    requires_human_verification: bool = False

class ExtractedConditionItem(BaseModel):
    condition_name: str = Field(..., description="Explicitly documented diagnosis, condition, or finding")
    onset_date: Optional[str] = Field(None, description="Documented date of onset if stated")
    source_page: int = Field(..., ge=1)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    source_snippet: Optional[str] = None
    requires_human_verification: bool = False

class ExtractedAllergyItem(BaseModel):
    allergen: str = Field(..., description="Documented substance or drug allergen")
    reaction: Optional[str] = Field(None, description="Documented allergic reaction")
    severity: Optional[str] = Field(None, description="Documented severity if explicitly stated")
    source_page: int = Field(..., ge=1)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    source_snippet: Optional[str] = None
    requires_human_verification: bool = False

class ExtractedPatientInfo(BaseModel):
    age: Optional[int] = Field(None, description="Patient age if explicitly stated")
    sex: Optional[str] = Field(None, description="Patient sex or gender if explicitly stated")
    symptoms: List[str] = Field(default_factory=list, description="Patient-reported symptoms explicitly mentioned")
    conditions: List[ExtractedConditionItem] = Field(default_factory=list)
    allergies: List[ExtractedAllergyItem] = Field(default_factory=list)
    medications: List[ExtractedMedicationItem] = Field(default_factory=list)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)

class ExtractedDocumentData(BaseModel):
    document_id: str
    patient_info: ExtractedPatientInfo
    laboratories: List[ExtractedLabItem] = Field(default_factory=list)
    extraction_notes: Optional[str] = Field(None, description="Summary of extraction quality or unverified flags")
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    has_unverified_items: bool = Field(default=False)
    processed_pages: List[int] = Field(default_factory=list)
