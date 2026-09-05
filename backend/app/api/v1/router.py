from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models import (
    Patient, 
    Document, 
    LabResult, 
    Medication, 
    Condition, 
    Allergy, 
    Observation,
    ConflictRecord, 
    TimelineEvent, 
    AuditLog,
    VerificationStatusEnum
)
from app.db.repositories import (
    PatientRepository,
    DocumentRepository,
    ClinicalRepository,
    ConflictRepository,
    TimelineRepository,
    AuditRepository,
    ProvenanceRepository,
)
from app.schemas.provenance import ClinicalProvenanceDetail
from app.schemas.verification import (
    VerificationQueueItem,
    VerificationActionRequest,
    VerificationActionResponse,
)
from app.schemas.patient import PatientRead, PatientDetail, PatientCreate
from app.schemas.document import DocumentRead, DocumentUploadResponse, DocumentPageRead, DocumentTextExtractionResponse
from app.schemas.clinical import LabResultRead, MedicationRead, ConditionRead, AllergyRead, ObservationRead
from app.schemas.ai_extraction import ExtractedDocumentData
from app.schemas.conflict import ConflictRecordRead, ConflictResolveRequest
from app.schemas.timeline import TimelineEventRead
from app.schemas.audit import AuditLogRead
from app.schemas.intake import PatientIntakeSubmission, PatientIntakeResponse
from app.services.intake_service import IntakeService
from app.services.document_service import DocumentService
from app.services.document_processor import DocumentProcessingService
from app.services.ai_extraction_service import AIExtractionService
from app.services.verification_service import VerificationService
from app.services.summary_service import SummaryService
from app.schemas.summary import ClinicalSummaryRead, ClinicalSummaryGenerateRequest
from app.db.seed import seed_synthetic_data


api_v1_router = APIRouter()

@api_v1_router.get("/")
def get_v1_root():
    return {
        "message": "MedLens API v1 operational",
        "description": "AI-Powered Clinical Information Intelligence API",
        "safety_notice": "MedLens is strictly non-diagnostic. Clinical reference ranges must originate solely from verified source reports."
    }

# --- Synthetic Demo Data Trigger ---
@api_v1_router.post("/seed", response_model=PatientRead)
def seed_demo_data(db: Session = Depends(get_db)):
    """Idempotently seeds realistic synthetic patient data for demonstrations."""
    patient = seed_synthetic_data(db)
    return patient

# --- Patient Intake Endpoints ---
@api_v1_router.post("/patients/intake", response_model=PatientIntakeResponse)
def submit_patient_intake(
    intake_in: PatientIntakeSubmission,
    db: Session = Depends(get_db)
):
    """
    Submit a new patient intake form.
    Validates demographics, clinical symptoms, conditions, allergies, medications.
    Labels all fields with PATIENT_INPUT provenance and creates an immutable AuditLog.
    """
    service = IntakeService(db)
    return service.submit_intake(intake_in, actor_name="Patient Intake Portal")

@api_v1_router.put("/patients/{patient_id}/intake", response_model=PatientIntakeResponse)
def update_patient_intake(
    patient_id: str,
    intake_in: PatientIntakeSubmission,
    db: Session = Depends(get_db)
):
    """
    Edit and update existing patient intake information.
    Preserves audit history and retains PATIENT_INPUT provenance.
    """
    service = IntakeService(db)
    updated = service.update_intake(patient_id, intake_in, actor_name="Patient Intake Editor")
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return updated

# --- Patients Endpoints ---
@api_v1_router.get("/patients", response_model=List[PatientRead])
def list_patients(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repo = PatientRepository(db)
    return repo.list_all(skip=skip, limit=limit)

@api_v1_router.get("/patients/{patient_id}", response_model=PatientDetail)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    repo = PatientRepository(db)
    patient = repo.get_detail(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# --- Documents Endpoints ---
@api_v1_router.post("/patients/{patient_id}/documents/upload", response_model=DocumentUploadResponse)
async def upload_patient_document(
    patient_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Securely uploads and indexes a medical document (PDF, PNG, JPG/JPEG).
    Validates file type and size, stores securely in isolated directory,
    calculates SHA-256 checksum, and initializes document status to UPLOADED.
    """
    service = DocumentService(db)
    doc = await service.upload_document(patient_id, file, actor_name="User Upload")
    return DocumentUploadResponse(
        id=doc.id,
        patient_id=doc.patient_id,
        filename=doc.filename,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        page_count=doc.page_count,
        processing_status=doc.processing_status,
        checksum=doc.checksum,
        upload_date=doc.upload_date,
        message="Medical document securely stored and registered"
    )

@api_v1_router.get("/patients/{patient_id}/documents", response_model=List[DocumentRead])
def get_patient_documents(patient_id: str, db: Session = Depends(get_db)):
    """List all medical documents registered to a patient."""
    service = DocumentService(db)
    return service.list_documents(patient_id)

@api_v1_router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata and pages for a specific document."""
    service = DocumentService(db)
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@api_v1_router.get("/documents/{document_id}/file")
def download_or_preview_document(document_id: str, db: Session = Depends(get_db)):
    """
    Securely streams the document to authenticated / authorized clients.
    Never exposes public URLs or filesystem directories.
    """
    service = DocumentService(db)
    file_path, original_name, mime_type = service.get_document_file(document_id)
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=original_name,
        content_disposition_type="inline"
    )

@api_v1_router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Deletes a medical document and removes its file from disk.
    Records an immutable audit log entry.
    """
    service = DocumentService(db)
    service.delete_document(document_id, actor_name="User")
    return {"status": "deleted", "id": document_id, "message": "Document successfully deleted"}

# --- Document Processing Pipeline ---
@api_v1_router.post("/documents/{document_id}/process", response_model=DocumentTextExtractionResponse)
def process_document_pipeline(document_id: str, db: Session = Depends(get_db)):
    """
    Executes medical document text extraction pipeline:
    Uploaded PDF -> PDF Validation -> Page Extraction -> Text Extraction -> Page-Level Storage -> Status.
    
    Treats document content as untrusted data.
    Does NOT perform medical interpretation at this stage.
    """
    processor = DocumentProcessingService(db)
    return processor.process_document(document_id)

@api_v1_router.get("/documents/{document_id}/pages", response_model=List[DocumentPageRead])
def get_document_pages(document_id: str, db: Session = Depends(get_db)):
    """Retrieves all stored pages with extracted text and extraction status for a document."""
    processor = DocumentProcessingService(db)
    return processor.get_document_pages(document_id)

# --- AI Medical Information Extraction ---
@api_v1_router.post("/documents/{document_id}/extract-medical-data", response_model=ExtractedDocumentData)
def extract_document_medical_data(document_id: str, db: Session = Depends(get_db)):
    """
    Executes AI Medical Information Extraction pipeline:
    Extracts demographics, conditions, allergies, medications, and laboratory values.
    Validates all data deterministically via ClinicalValidationGate before persisting.
    Never invents reference ranges or diagnoses.
    """
    ai_service = AIExtractionService(db)
    return ai_service.extract_document_medical_data(document_id)



# --- Clinical Endpoints ---
@api_v1_router.get("/patients/{patient_id}/labs", response_model=List[LabResultRead])
def get_patient_labs(patient_id: str, db: Session = Depends(get_db)):
    repo = ClinicalRepository(db)
    return repo.list_labs_by_patient(patient_id)

@api_v1_router.get("/patients/{patient_id}/medications", response_model=List[MedicationRead])
def get_patient_medications(patient_id: str, db: Session = Depends(get_db)):
    repo = ClinicalRepository(db)
    return repo.list_meds_by_patient(patient_id)

@api_v1_router.get("/patients/{patient_id}/allergies", response_model=List[AllergyRead])
def get_patient_allergies(patient_id: str, db: Session = Depends(get_db)):
    repo = ClinicalRepository(db)
    return repo.list_allergies_by_patient(patient_id)

@api_v1_router.get("/patients/{patient_id}/conditions", response_model=List[ConditionRead])
def get_patient_conditions(patient_id: str, db: Session = Depends(get_db)):
    repo = ClinicalRepository(db)
    return repo.list_conditions_by_patient(patient_id)

@api_v1_router.get("/patients/{patient_id}/observations", response_model=List[ObservationRead])
def get_patient_observations(patient_id: str, db: Session = Depends(get_db)):
    repo = ClinicalRepository(db)
    return repo.list_observations_by_patient(patient_id)

class ClinicalItemVerifyRequest(BaseModel):
    entity_type: str  # "lab" | "medication" | "condition" | "allergy" | "observation"
    entity_id: str
    verification_status: str = "VERIFIED"  # "VERIFIED" | "DISPUTED" | "REJECTED"
    verified_by: str = "Clinician Reviewer"
    verification_notes: Optional[str] = None

@api_v1_router.post("/clinical/verify-item")
def verify_clinical_item(
    payload: ClinicalItemVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Human verification endpoint for clinical entities.
    Transitions UNVERIFIED items to VERIFIED or DISPUTED with immutable audit logging.
    """
    entity_map = {
        "lab": LabResult,
        "medication": Medication,
        "condition": Condition,
        "allergy": Allergy,
        "observation": Observation,
    }
    model = entity_map.get(payload.entity_type.lower())
    if not model:
        raise HTTPException(status_code=400, detail=f"Invalid entity type '{payload.entity_type}'")

    item = db.query(model).filter(model.id == payload.entity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Clinical entity not found")

    old_status = getattr(item, "verification_status", None)
    new_status_str = payload.verification_status.upper()
    try:
        new_status_enum = VerificationStatusEnum[new_status_str]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid verification status '{new_status_str}'")

    item.verification_status = new_status_enum
    item.verified_by = payload.verified_by
    item.verified_at = datetime.utcnow()

    # Immutable Audit Log
    audit = AuditLog(
        entity_type=model.__name__,
        entity_id=item.id,
        action="HUMAN_VERIFICATION",
        actor_id="CLINICIAN",
        actor_name=payload.verified_by,
        previous_state=str(old_status.value if old_status else "UNKNOWN"),
        new_state=new_status_enum.value,
        change_reason=payload.verification_notes or "Clinician manual verification review",
    )
    db.add(audit)
    db.commit()
    db.refresh(item)
    return {
        "status": "success",
        "entity_type": payload.entity_type,
        "entity_id": item.id,
        "verification_status": new_status_enum.value,
        "verified_by": payload.verified_by,
        "verified_at": item.verified_at.isoformat()
    }

@api_v1_router.get("/clinical/{entity_type}/{entity_id}/provenance", response_model=ClinicalProvenanceDetail)
def get_clinical_item_provenance(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full immutable provenance metadata for any clinical entity:
    Source type (PATIENT_INPUT, DOCUMENT_EXTRACTION, AI_GENERATED, HUMAN_VERIFIED),
    Document ID, original filename, page number, extraction timestamp, confidence score,
    and unedited verbatim source snippet.
    """
    repo = ProvenanceRepository(db)
    detail = repo.get_entity_provenance(entity_type, entity_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Provenance record not found for entity")
    return detail

# --- Human Verification Workflow Endpoints ---
@api_v1_router.get("/clinical/verification-queue", response_model=List[VerificationQueueItem])
def get_verification_queue(
    patient_id: Optional[str] = Query(None, description="Filter queue by patient UUID"),
    db: Session = Depends(get_db)
):
    """
    Returns clinical items in the Human Verification Queue:
    - Low extraction confidence (< 90%)
    - Ambiguity / missing reference range (UNKNOWN)
    - Conflicting documentation across records
    - Manual confirmation required (UNVERIFIED)
    """
    service = VerificationService(db)
    return service.get_verification_queue(patient_id=patient_id)

@api_v1_router.post("/clinical/verify-action", response_model=VerificationActionResponse)
def execute_verification_action(
    payload: VerificationActionRequest,
    db: Session = Depends(get_db)
):
    """
    Executes human clinician verification action: ACCEPT, EDIT, or REJECT.
    - Preserves original AI extraction (raw_value/raw_text is NEVER deleted).
    - When edited: stores corrected_value, verifier name, and timestamp.
    - Records signed VerificationRecord and immutable AuditLog entry.
    """
    service = VerificationService(db)
    return service.execute_verification_action(payload)




# --- Conflict Endpoints ---
@api_v1_router.get("/patients/{patient_id}/conflicts", response_model=List[ConflictRecordRead])
def get_patient_conflicts(
    patient_id: str, 
    status: Optional[str] = Query(None, description="UNRESOLVED, RESOLVED, DISMISSED"),
    db: Session = Depends(get_db)
):
    repo = ConflictRepository(db)
    return repo.list_by_patient(patient_id, status=status)

@api_v1_router.post("/conflicts/{conflict_id}/resolve", response_model=ConflictRecordRead)
def resolve_conflict(
    conflict_id: str,
    resolve_in: ConflictResolveRequest,
    db: Session = Depends(get_db)
):
    repo = ConflictRepository(db)
    resolved = repo.resolve(conflict_id, resolve_in)
    if not resolved:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return resolved

# --- Timeline Endpoints ---
@api_v1_router.get("/patients/{patient_id}/timeline", response_model=List[TimelineEventRead])
def get_patient_timeline(patient_id: str, db: Session = Depends(get_db)):
    repo = TimelineRepository(db)
    return repo.list_by_patient(patient_id)

# --- Audit History Endpoints ---
@api_v1_router.get("/patients/{patient_id}/audit", response_model=List[AuditLogRead])
def get_patient_audit_logs(patient_id: str, db: Session = Depends(get_db)):
    repo = AuditRepository(db)
    return repo.list_by_entity(entity_type="Patient", entity_id=patient_id)


# --- Clinical AI Summary Endpoints ---
@api_v1_router.get("/patients/{patient_id}/summary", response_model=Optional[ClinicalSummaryRead])
def get_patient_clinical_summary(patient_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the latest clinical summary for a patient.
    Returns 7 structured sections, provenance record IDs, and mandatory non-diagnostic disclaimer.
    """
    service = SummaryService(db)
    return service.get_patient_summary(patient_id)


@api_v1_router.post("/patients/{patient_id}/summary/generate", response_model=ClinicalSummaryRead)
def generate_patient_clinical_summary(
    patient_id: str,
    payload: Optional[ClinicalSummaryGenerateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Generates a patient-friendly clinical summary ONLY from validated structured patient records.
    Produces 7 structured sections:
    1. Record overview
    2. Recently documented information
    3. Laboratory values and their source-report status
    4. Historical changes
    5. Potential conflicts
    6. Missing information
    7. Verification-required information

    Strictly non-diagnostic with report-derived reference intervals only.
    Stores summary provenance recording all structured entity IDs used.
    """
    service = SummaryService(db)
    force = payload.force_regenerate if payload else True
    return service.generate_summary(patient_id, force_regenerate=force)
