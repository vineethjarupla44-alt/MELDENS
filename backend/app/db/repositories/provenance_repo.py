from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import (
    LabResult,
    Medication,
    Condition,
    Allergy,
    Observation,
    Document,
    ProvenanceRecord,
)
from app.schemas.provenance import ClinicalProvenanceDetail, ProvenanceSource, VerificationStatus

class ProvenanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_entity_provenance(self, entity_type: str, entity_id: str) -> Optional[ClinicalProvenanceDetail]:
        """
        Retrieves complete provenance traceability for any clinical entity.
        Strictly preserves original source data without modification.
        """
        etype = entity_type.lower()
        model_map = {
            "lab": LabResult,
            "medication": Medication,
            "condition": Condition,
            "allergy": Allergy,
            "observation": Observation,
        }

        model = model_map.get(etype)
        if not model:
            return None

        item = self.db.query(model).filter(model.id == entity_id).first()
        if not item:
            return None

        # Determine item name, formatted value, and unedited raw value
        if etype == "lab":
            item_name = item.test_name
            item_value = f"{item.value} {item.unit or ''}".strip() if item.value is not None else (item.raw_value or "N/A")
            raw_val = item.raw_value
        elif etype == "medication":
            item_name = item.medication_name
            parts = [p for p in [item.dosage, item.frequency, f"({item.route})" if item.route else ""] if p]
            item_value = " · ".join(parts) if parts else "Prescribed"
            raw_val = item.raw_text
        elif etype == "condition":
            item_name = item.condition_name
            item_value = f"Status: {item.clinical_status}" + (f" (Onset: {item.onset_date})" if item.onset_date else "")
            raw_val = item.raw_text
        elif etype == "allergy":
            item_name = item.allergen
            parts = [p for p in [item.reaction, f"Severity: {item.severity}" if item.severity else ""] if p]
            item_value = " — ".join(parts) if parts else "Documented Allergy"
            raw_val = item.raw_text
        elif etype == "observation":
            item_name = item.observation_name or item.observation_type
            item_value = f"{item.numeric_value or item.string_value or ''} {item.unit or ''}".strip()
            raw_val = item.string_value or str(item.numeric_value) if item.numeric_value is not None else None
        else:
            item_name = "Clinical Finding"
            item_value = None
            raw_val = None

        # Resolve human-readable method
        source_enum_val = item.provenance_source.value if hasattr(item, "provenance_source") and item.provenance_source else "DOCUMENT_EXTRACTION"
        if source_enum_val == "PATIENT_INPUT":
            method_label = "Patient Self-Report Intake"
        elif source_enum_val == "AI_GENERATED":
            method_label = "AI Information Extraction"
        elif source_enum_val == "HUMAN_VERIFIED":
            method_label = "Clinician Verified Entry"
        else:
            method_label = "Document Extraction Pipeline"

        # Resolve document filename
        doc_filename = item.source_document
        if not doc_filename and item.document_id:
            doc = self.db.query(Document).filter(Document.id == item.document_id).first()
            if doc:
                doc_filename = doc.original_name or doc.filename

        doc_stream_url = f"/api/v1/documents/{item.document_id}/file" if item.document_id else None

        return ClinicalProvenanceDetail(
            entity_type=etype,
            entity_id=item.id,
            item_name=item_name,
            item_value=item_value,
            raw_value=raw_val,
            source_type=ProvenanceSource(source_enum_val),
            method=method_label,
            document_id=item.document_id,
            filename=doc_filename,
            page_number=item.source_page,
            extraction_timestamp=item.created_at,
            confidence=item.confidence,
            verification_status=VerificationStatus(item.verification_status.value if item.verification_status else "UNVERIFIED"),
            verified_by=item.verified_by,
            verified_at=item.verified_at,
            source_snippet=item.source_snippet,
            document_stream_url=doc_stream_url,
        )
