"""
MedLens Phase 2 Data Layer Verification Test Suite
Tests:
- Patient & PatientProfile
- Multi-document & Multi-page relationships
- Strict report-only reference range deterministic evaluator
- NULL reference range rule (never auto-populate, returns UNKNOWN)
- Provenance source types & metadata
- Conflict records & resolution
- Timeline & Audit trail
"""
import sys
from app.db.session import SessionLocal, Base, engine
from app.db.models import (
    Patient,
    Document,
    DocumentPage,
    LabResult,
    Medication,
    ConflictRecord,
    TimelineEvent,
    AuditLog,
    LabStatusEnum,
    ConflictStatusEnum,
)
from app.db.repositories.clinical_repo import evaluate_lab_status
from app.db.seed import seed_synthetic_data

def test_database_integrity():
    db = SessionLocal()
    try:
        print("\n--- Running MedLens Phase 2 Data Layer Tests ---")

        # 1. Seed or retrieve synthetic patient
        patient = seed_synthetic_data(db)
        assert patient is not None, "Failed to seed or retrieve synthetic patient"
        print(f"PASS: Patient verified -> {patient.first_name} {patient.last_name} (MRN: {patient.mrn})")

        # 2. Verify Profile relationship
        assert patient.profile is not None, "PatientProfile missing"
        assert patient.profile.preferred_language == "English"
        print(f"PASS: PatientProfile verified -> Language: {patient.profile.preferred_language}, Emergency: {patient.profile.emergency_contact_name}")

        # 3. Verify Multi-Document & Multi-Page requirements
        docs = db.query(Document).filter(Document.patient_id == patient.id).all()
        assert len(docs) >= 3, f"Expected >= 3 documents, found {len(docs)}"
        print(f"PASS: Multi-document verified -> Patient has {len(docs)} documents")

        multi_page_doc = next((d for d in docs if d.page_count > 1), None)
        assert multi_page_doc is not None, "No multi-page document found"
        pages = db.query(DocumentPage).filter(DocumentPage.document_id == multi_page_doc.id).all()
        assert len(pages) == multi_page_doc.page_count, f"Page count mismatch: {len(pages)} vs {multi_page_doc.page_count}"
        print(f"PASS: Multi-page document verified -> '{multi_page_doc.filename}' has {len(pages)} pages")

        # 4. Strict Laboratory Reference Range Rules
        labs = db.query(LabResult).filter(LabResult.patient_id == patient.id).all()
        assert len(labs) >= 3, f"Expected >= 3 labs, found {len(labs)}"

        # 4a. Lab with Low value
        hgb = next((l for l in labs if l.test_name == "Hemoglobin"), None)
        assert hgb is not None
        assert hgb.value == 11.2
        assert hgb.reference_range_low == 12.0
        assert hgb.reference_range_high == 16.0
        assert hgb.status == LabStatusEnum.LOW, f"Expected LOW status, got {hgb.status}"
        print(f"PASS: Report-derived range LOW verified -> Hemoglobin {hgb.value} {hgb.unit} (Ref: {hgb.reference_range_text}) -> {hgb.status.value}")

        # 4b. Lab with Normal value
        glu = next((l for l in labs if l.test_name == "Fasting Blood Glucose"), None)
        assert glu is not None
        assert glu.status == LabStatusEnum.NORMAL
        print(f"PASS: Report-derived range NORMAL verified -> Fasting Glucose {glu.value} {glu.unit} -> {glu.status.value}")

        # 4c. Lab with NULL reference range (Must be UNKNOWN, NEVER auto-populated!)
        fer = next((l for l in labs if l.test_name == "Serum Ferritin"), None)
        assert fer is not None
        assert fer.reference_range_low is None, "reference_range_low must be None"
        assert fer.reference_range_high is None, "reference_range_high must be None"
        assert fer.reference_range_text is None, "reference_range_text must be None"
        assert fer.status == LabStatusEnum.UNKNOWN, f"Missing reference range must evaluate to UNKNOWN, got {fer.status}"
        print(f"PASS: Missing reference range UNKNOWN rule verified -> Ferritin range is NULL -> status: {fer.status.value}")

        # 5. Unit test deterministic evaluator directly
        assert evaluate_lab_status(11.2, 12.0, 16.0) == LabStatusEnum.LOW
        assert evaluate_lab_status(14.0, 12.0, 16.0) == LabStatusEnum.NORMAL
        assert evaluate_lab_status(17.5, 12.0, 16.0) == LabStatusEnum.HIGH
        assert evaluate_lab_status(15.0, None, None) == LabStatusEnum.UNKNOWN
        assert evaluate_lab_status(None, 12.0, 16.0) == LabStatusEnum.UNKNOWN
        print("PASS: evaluate_lab_status unit tests passed (5/5 assertions)")

        # 6. Verify Provenance Tracking on every entity
        for l in labs:
            assert l.provenance_source in ["DOCUMENT_EXTRACTION", "PATIENT_INPUT", "AI_GENERATED", "HUMAN_VERIFIED"]
            assert l.source_document is not None
            assert l.source_page is not None
        print("PASS: Provenance tracking metadata verified across all lab results")

        # 7. Verify Cross-Source Conflicts
        conflicts = db.query(ConflictRecord).filter(ConflictRecord.patient_id == patient.id).all()
        assert len(conflicts) >= 2, f"Expected >= 2 conflicts, found {len(conflicts)}"
        allergy_conflict = next((c for c in conflicts if c.category.value == "ALLERGY"), None)
        assert allergy_conflict is not None
        assert "Penicillin" in allergy_conflict.source_a_value
        assert "NKDA" in allergy_conflict.source_b_value
        assert allergy_conflict.status == ConflictStatusEnum.UNRESOLVED
        print(f"PASS: Allergy conflict verified -> '{allergy_conflict.source_a_value}' vs '{allergy_conflict.source_b_value}'")

        # 8. Verify Timeline Events
        events = db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient.id).all()
        assert len(events) >= 3
        print(f"PASS: Chronological timeline verified ({len(events)} events)")

        # 9. Verify Audit Trail
        audit_logs = db.query(AuditLog).filter(AuditLog.entity_id == patient.id).all()
        assert len(audit_logs) >= 1
        print(f"PASS: Audit log verified ({len(audit_logs)} logs)")

        print("\n ALL PHASE 2 DATA LAYER TESTS PASSED SUCCESSFULLY!")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    success = test_database_integrity()
    sys.exit(0 if success else 1)
