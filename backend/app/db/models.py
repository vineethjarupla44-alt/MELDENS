import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

# --- Enums ---

class ProvenanceSourceEnum(str, enum.Enum):
    PATIENT_INPUT = "PATIENT_INPUT"
    DOCUMENT_EXTRACTION = "DOCUMENT_EXTRACTION"
    AI_GENERATED = "AI_GENERATED"
    HUMAN_VERIFIED = "HUMAN_VERIFIED"

class VerificationStatusEnum(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"

class LabStatusEnum(str, enum.Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"

class ConflictStatusEnum(str, enum.Enum):
    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class ConflictCategoryEnum(str, enum.Enum):
    ALLERGY = "ALLERGY"
    MEDICATION = "MEDICATION"
    LAB_RESULT = "LAB_RESULT"
    DEMOGRAPHIC = "DEMOGRAPHIC"
    OTHER = "OTHER"

class DocumentStatusEnum(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

# --- Models ---

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mrn = Column(String(50), unique=True, index=True, nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(String(20), nullable=True)
    gender = Column(String(20), nullable=True)
    blood_type = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 1:1 Profile
    profile = relationship("PatientProfile", back_populates="patient", uselist=False, cascade="all, delete-orphan")

    # 1:N Collections
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    conditions = relationship("Condition", back_populates="patient", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="patient", cascade="all, delete-orphan")
    conflicts = relationship("ConflictRecord", back_populates="patient", cascade="all, delete-orphan")
    summaries = relationship("ClinicalSummary", back_populates="patient", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="patient", cascade="all, delete-orphan")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), unique=True, nullable=False, index=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    preferred_language = Column(String(50), default="English")
    insurance_provider = Column(String(100), nullable=True)
    baseline_notes = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="profile")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(50), default="UPLOADED")
    raw_text = Column(Text, nullable=True)
    page_count = Column(Integer, default=1)
    checksum = Column(String(64), nullable=True)

    patient = relationship("Patient", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="document")
    medications = relationship("Medication", back_populates="document")
    conditions = relationship("Condition", back_populates="document")
    allergies = relationship("Allergy", back_populates="document")
    observations = relationship("Observation", back_populates="document")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False) # 1-indexed
    extracted_text = Column(Text, nullable=True)
    ocr_applied = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    image_path = Column(String(255), nullable=True)
    extraction_status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="pages")
    lab_results = relationship("LabResult", back_populates="page")
    medications = relationship("Medication", back_populates="page")
    conditions = relationship("Condition", back_populates="page")
    allergies = relationship("Allergy", back_populates="page")
    observations = relationship("Observation", back_populates="page")


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=True, index=True)

    test_name = Column(String(200), nullable=False, index=True)
    raw_value = Column(String(100), nullable=True) # Preserves exact original string
    corrected_value = Column(String(200), nullable=True) # Clinician corrected/edited value
    value = Column(Float, nullable=True)           # Parsed numeric
    unit = Column(String(50), nullable=True)


    # Reference ranges strictly from report; NULL allowed, NEVER auto-populated
    reference_range_low = Column(Float, nullable=True)
    reference_range_high = Column(Float, nullable=True)
    reference_range_text = Column(String(100), nullable=True)
    status = Column(SQLEnum(LabStatusEnum), default=LabStatusEnum.UNKNOWN, nullable=False)
    report_date = Column(String(50), nullable=True)

    # Provenance tracking
    provenance_source = Column(SQLEnum(ProvenanceSourceEnum), default=ProvenanceSourceEnum.DOCUMENT_EXTRACTION, nullable=False)
    source_document = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    source_snippet = Column(Text, nullable=True)
    verification_status = Column(SQLEnum(VerificationStatusEnum), default=VerificationStatusEnum.UNVERIFIED, nullable=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="lab_results")
    document = relationship("Document", back_populates="lab_results")
    page = relationship("DocumentPage", back_populates="lab_results")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=True, index=True)

    medication_name = Column(String(200), nullable=False, index=True)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    route = Column(String(50), nullable=True)
    clinical_status = Column(String(50), default="ACTIVE")
    prescribed_date = Column(String(50), nullable=True)
    raw_text = Column(Text, nullable=True)
    corrected_value = Column(String(200), nullable=True)

    # Provenance
    provenance_source = Column(SQLEnum(ProvenanceSourceEnum), default=ProvenanceSourceEnum.DOCUMENT_EXTRACTION, nullable=False)
    source_document = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    source_snippet = Column(Text, nullable=True)
    verification_status = Column(SQLEnum(VerificationStatusEnum), default=VerificationStatusEnum.UNVERIFIED, nullable=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medications")
    document = relationship("Document", back_populates="medications")
    page = relationship("DocumentPage", back_populates="medications")


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=True, index=True)

    condition_name = Column(String(255), nullable=False, index=True)
    icd10_code = Column(String(20), nullable=True)
    onset_date = Column(String(50), nullable=True)
    clinical_status = Column(String(50), default="ACTIVE")
    raw_text = Column(Text, nullable=True)
    corrected_value = Column(String(200), nullable=True)

    # Provenance
    provenance_source = Column(SQLEnum(ProvenanceSourceEnum), default=ProvenanceSourceEnum.DOCUMENT_EXTRACTION, nullable=False)
    source_document = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    source_snippet = Column(Text, nullable=True)
    verification_status = Column(SQLEnum(VerificationStatusEnum), default=VerificationStatusEnum.UNVERIFIED, nullable=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="conditions")
    document = relationship("Document", back_populates="conditions")
    page = relationship("DocumentPage", back_populates="conditions")


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=True, index=True)

    allergen = Column(String(200), nullable=False, index=True)
    reaction = Column(String(200), nullable=True)
    severity = Column(String(50), nullable=True)
    raw_text = Column(Text, nullable=True)
    corrected_value = Column(String(200), nullable=True)

    # Provenance
    provenance_source = Column(SQLEnum(ProvenanceSourceEnum), default=ProvenanceSourceEnum.DOCUMENT_EXTRACTION, nullable=False)
    source_document = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    source_snippet = Column(Text, nullable=True)
    verification_status = Column(SQLEnum(VerificationStatusEnum), default=VerificationStatusEnum.UNVERIFIED, nullable=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="allergies")
    document = relationship("Document", back_populates="allergies")
    page = relationship("DocumentPage", back_populates="allergies")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    page_id = Column(String(36), ForeignKey("document_pages.id"), nullable=True, index=True)

    observation_type = Column(String(100), nullable=False, index=True) # e.g. BLOOD_PRESSURE, HEART_RATE, SPO2, BMI
    observation_name = Column(String(200), nullable=False)
    numeric_value = Column(Float, nullable=True)
    string_value = Column(String(100), nullable=True)
    corrected_value = Column(String(200), nullable=True)
    unit = Column(String(50), nullable=True)
    observation_date = Column(String(50), nullable=True)


    # Provenance
    provenance_source = Column(SQLEnum(ProvenanceSourceEnum), default=ProvenanceSourceEnum.DOCUMENT_EXTRACTION, nullable=False)
    source_document = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    source_snippet = Column(Text, nullable=True)
    verification_status = Column(SQLEnum(VerificationStatusEnum), default=VerificationStatusEnum.UNVERIFIED, nullable=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="observations")
    document = relationship("Document", back_populates="observations")
    page = relationship("DocumentPage", back_populates="observations")


class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False, index=True) # LabResult, Medication, etc.
    entity_id = Column(String(36), nullable=False, index=True)
    source_type = Column(SQLEnum(ProvenanceSourceEnum), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    document_name = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    extraction_confidence = Column(Float, nullable=True)
    raw_extracted_text = Column(Text, nullable=True)
    extraction_method = Column(String(100), default="PDF_PARSER")
    created_at = Column(DateTime, default=datetime.utcnow)


class ConflictRecord(Base):
    __tablename__ = "conflicts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    category = Column(SQLEnum(ConflictCategoryEnum), nullable=False)
    field_name = Column(String(100), nullable=False)

    source_a_type = Column(String(50), nullable=False)
    source_a_document = Column(String(255), nullable=True)
    source_a_page = Column(Integer, nullable=True)
    source_a_value = Column(Text, nullable=False)

    source_b_type = Column(String(50), nullable=False)
    source_b_document = Column(String(255), nullable=True)
    source_b_page = Column(Integer, nullable=True)
    source_b_value = Column(Text, nullable=False)

    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(SQLEnum(ConflictStatusEnum), default=ConflictStatusEnum.UNRESOLVED, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="conflicts")


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    reviewer_id = Column(String(100), nullable=False)
    reviewer_name = Column(String(100), nullable=False)
    reviewer_role = Column(String(100), nullable=False)
    action = Column(String(20), default="ACCEPT") # ACCEPT, EDIT, REJECT
    original_value = Column(Text, nullable=True) # Unmodified AI extracted string
    corrected_value = Column(Text, nullable=True) # Human-verified corrected value
    status = Column(SQLEnum(VerificationStatusEnum), nullable=False)
    notes = Column(Text, nullable=True)
    signed_at = Column(DateTime, default=datetime.utcnow)



class ClinicalSummary(Base):
    __tablename__ = "clinical_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    sections = Column(Text, nullable=True) # JSON serialized 7 sections
    structured_provenance_sources = Column(Text, nullable=True) # JSON serialized record IDs used
    key_findings = Column(Text, nullable=True) # JSON serialized list of finding highlights
    disclaimer = Column(
        Text, 
        default="MedLens organizes and explains information contained in the available records. It does not provide medical diagnosis or treatment recommendations."
    )
    model_version = Column(String(50), default="medlens-summary-v1")
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="summaries")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    event_date = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # LAB_TEST, MEDICATION_ACTIVE, CONDITION_ONSET, VITAL_SIGN, ENCOUNTER
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(36), nullable=True)
    source_document = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    importance = Column(String(20), default="ROUTINE") # ROUTINE, SIGNIFICANT, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="timeline_events")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False) # CREATE, UPDATE, VERIFY, RESOLVE_CONFLICT, DELETE
    actor_id = Column(String(100), default="SYSTEM")
    actor_name = Column(String(100), default="System Engine")
    previous_state = Column(Text, nullable=True)
    new_state = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
