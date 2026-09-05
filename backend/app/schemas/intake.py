from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.schemas.provenance import ProvenanceSource, VerificationStatus

class ConditionIntakeItem(BaseModel):
    condition_name: str = Field(..., min_length=2, description="Name of diagnosed medical condition")
    onset_date: Optional[str] = Field(None, description="Approximate onset year or date")
    clinical_status: str = Field(default="ACTIVE", description="ACTIVE or RESOLVED")

class AllergyIntakeItem(BaseModel):
    allergen: str = Field(..., min_length=2, description="Allergen name (e.g., Penicillin, Latex, Peanuts)")
    reaction: Optional[str] = Field(None, description="Observed allergic reaction (e.g., Hives, Anaphylaxis)")
    severity: str = Field(default="MODERATE", description="MILD, MODERATE, or SEVERE")

class MedicationIntakeItem(BaseModel):
    medication_name: str = Field(..., min_length=2, description="Medication name")
    dosage: Optional[str] = Field(None, description="Dosage (e.g., 500 mg, 10 units)")
    frequency: Optional[str] = Field(None, description="Frequency (e.g., Once daily, Twice daily)")
    route: str = Field(default="Oral", description="Oral, Inhalation, Topical, Injection, etc.")

class PatientIntakeSubmission(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="Patient first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Patient last name")
    date_of_birth: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Birth date in YYYY-MM-DD format")
    gender: str = Field(..., description="Biological sex / gender: Male, Female, Other, Unknown")
    blood_type: Optional[str] = Field(None, description="Blood type ABO/Rh (e.g. A+, O-, B+)")
    mrn: Optional[str] = Field(None, description="Optional Medical Record Number; generated if omitted")
    
    # Clinical Intake Fields
    symptoms: Optional[str] = Field(None, description="Patient-reported present symptoms and chief complaints")
    existing_conditions: List[ConditionIntakeItem] = Field(default_factory=list, description="Patient-reported existing medical conditions")
    allergies: List[AllergyIntakeItem] = Field(default_factory=list, description="Patient-reported known drug and environmental allergies")
    current_medications: List[MedicationIntakeItem] = Field(default_factory=list, description="Patient-reported active prescription and OTC medications")
    additional_notes: Optional[str] = Field(None, description="Any additional health background, surgical history, or comments")

    # Optional emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    preferred_language: str = "English"

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        valid_genders = ["Male", "Female", "Other", "Unknown", "Non-Binary"]
        for g in valid_genders:
            if v.strip().lower() == g.lower():
                return g
        return v.strip().capitalize()

class PatientIntakeResponse(BaseModel):
    patient_id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    blood_type: Optional[str] = None
    symptoms: Optional[str] = None
    additional_notes: Optional[str] = None
    provenance_source: str = "PATIENT_INPUT"
    conditions_count: int
    allergies_count: int
    medications_count: int
    created_at: datetime
    updated_at: datetime
    audit_id: str

    class Config:
        from_attributes = True
