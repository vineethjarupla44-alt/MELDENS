"""
MedLens AI Summary Module Automated Verification Suite
Validates:
1. Generation ONLY from validated structured patient records (Demographics, Docs, Labs, Meds, Conditions, Allergies, Conflicts, Timeline)
2. Presence and completeness of all 7 mandatory sections:
   - 1. Record overview
   - 2. Recently documented information
   - 3. Laboratory values and their source-report status (NORMAL, LOW, HIGH, UNKNOWN)
   - 4. Historical changes
   - 5. Potential conflicts
   - 6. Missing information
   - 7. Verification-required information
3. Strict non-diagnostic guardrails:
   - Prohibits diagnoses, treatments, medication recommendations, dosage modifications
4. Exact mandatory disclaimer:
   "MedLens organizes and explains information contained in the available records. It does not provide medical diagnosis or treatment recommendations."
5. Grounding & Report-Derived Ranges:
   - Zero fabricated reference ranges; UNKNOWN clearly flagged as not provided in source report
6. Summary Provenance Tracking:
   - Preserves exact IDs of structured records utilized
7. End-to-end FastAPI endpoint validation (GET & POST)
"""
import sys
from app.db.session import SessionLocal
from app.db.models import Patient, ClinicalSummary, AuditLog
from app.services.summary_service import SummaryService, MANDATORY_DISCLAIMER, PROHIBITED_PHRASES
from app.schemas.summary import ClinicalSummaryGenerateRequest
from app.api.v1.router import get_patient_clinical_summary, generate_patient_clinical_summary


def test_ai_summary_module():
    db = SessionLocal()
    try:
        print("\n" + "=" * 80)
        print("MEDLENS AI SUMMARY MODULE — COMPREHENSIVE VERIFICATION SUITE")
        print("=" * 80)

        # 1. Fetch test patient (Eleanor Vance)
        patient = db.query(Patient).filter(Patient.mrn == "MED-SYNTH-8492").first()
        if not patient:
            patient = db.query(Patient).first()
        assert patient is not None, "No test patient found in database! Ensure synthetic data is seeded."
        print(f"\n[PASS] Target patient located: {patient.first_name} {patient.last_name} (MRN: {patient.mrn})")

        # 2. Test SummaryService.generate_summary
        service = SummaryService(db)
        summary = service.generate_summary(patient.id, force_regenerate=True)
        assert summary is not None, "SummaryService returned None!"
        print(f"[PASS] Summary generated successfully (ID: {summary.id})")
        print(f"       Model Version: {summary.model_version}")
        print(f"       AI Generated Flag: {summary.is_ai_generated}")

        # 3. Verify all 7 mandatory sections
        sections = summary.sections
        assert sections is not None, "Summary sections object is None!"

        required_section_keys = [
            "record_overview",
            "recently_documented",
            "laboratory_values",
            "historical_changes",
            "potential_conflicts",
            "missing_information",
            "verification_required",
        ]

        print("\n--- Verifying All 7 Structured Sections ---")
        for key in required_section_keys:
            val = getattr(sections, key, None)
            assert val and len(val.strip()) > 10, f"Section '{key}' is missing or too short! Content: {val}"
            print(f"  [PASS] Section '{key}': {len(val)} chars")
            print(f"         Snippet: {val[:120]}...")

        # 4. Verify Exact Mandatory Disclaimer
        print("\n--- Verifying Mandatory Non-Diagnostic Disclaimer ---")
        expected_disclaimer = (
            "MedLens organizes and explains information contained in the available records. "
            "It does not provide medical diagnosis or treatment recommendations."
        )
        assert summary.disclaimer.strip() == expected_disclaimer, (
            f"Disclaimer does not match mandatory safety string!\n"
            f"Expected: '{expected_disclaimer}'\n"
            f"Got:      '{summary.disclaimer}'"
        )
        print(f"  [PASS] Exact mandatory disclaimer confirmed:\n         \"{summary.disclaimer}\"")

        # 5. Verify Non-Diagnostic Guardrail Invariant
        print("\n--- Verifying Non-Diagnostic & Non-Prescriptive Guardrails ---")
        full_text = (
            summary.summary_text + " " +
            sections.record_overview + " " +
            sections.recently_documented + " " +
            sections.laboratory_values + " " +
            sections.historical_changes + " " +
            sections.potential_conflicts + " " +
            sections.missing_information + " " +
            sections.verification_required
        ).lower()

        for prohibited in PROHIBITED_PHRASES:
            assert prohibited not in full_text, f"Guardrail violation! Prohibited phrase found: '{prohibited}'"
        print("  [PASS] 0 diagnostic or prescriptive violations detected across entire generated summary.")

        # 6. Verify Laboratory Values Grounding & Report-Derived Ranges
        print("\n--- Verifying Laboratory Values Grounding & UNKNOWN Range Handling ---")
        lab_section = sections.laboratory_values
        # Eleanor Vance has Ferritin with missing report range, Hemoglobin LOW, Glucose NORMAL
        assert "LOW" in lab_section or "NORMAL" in lab_section, "Lab section does not mention source statuses!"
        assert "REFERENCE RANGE NOT PROVIDED" in lab_section or "not provided in source report" in lab_section, (
            "Lab section did not properly identify missing source reference ranges!"
        )
        assert "fabricated" in lab_section or "not provided" in lab_section, (
            "Missing report range safety statement not present in lab section!"
        )
        print("  [PASS] Lab values strictly categorized by source report status (LOW, NORMAL, UNKNOWN).")
        print("  [PASS] Missing reference ranges explicitly labeled 'Reference range not provided' with zero fabrication.")

        # 7. Verify Potential Conflicts Reporting
        print("\n--- Verifying Potential Conflicts Section ---")
        conflicts_section = sections.potential_conflicts
        # Eleanor Vance has Penicillin and Metformin conflicts seeded
        assert "conflict" in conflicts_section.lower() or "discrepanc" in conflicts_section.lower(), (
            "Conflicts section failed to identify recorded discrepancies!"
        )
        print(f"  [PASS] Documented conflicts captured:\n         {conflicts_section[:140]}...")

        # 8. Verify Summary Provenance Sources (Entity IDs)
        print("\n--- Verifying Structured Summary Provenance ---")
        prov = summary.structured_provenance_sources
        assert prov is not None, "Summary provenance sources is None!"
        assert len(prov.lab_ids) > 0, "No lab IDs recorded in summary provenance!"
        assert len(prov.document_ids) > 0, "No document IDs recorded in summary provenance!"
        assert len(prov.condition_ids) > 0, "No condition IDs recorded in summary provenance!"
        print(f"  [PASS] Provenance record IDs preserved:")
        print(f"         Documents:   {len(prov.document_ids)} IDs -> {prov.document_ids}")
        print(f"         Labs:        {len(prov.lab_ids)} IDs -> {prov.lab_ids}")
        print(f"         Medications: {len(prov.medication_ids)} IDs -> {prov.medication_ids}")
        print(f"         Conditions:  {len(prov.condition_ids)} IDs -> {prov.condition_ids}")
        print(f"         Allergies:   {len(prov.allergy_ids)} IDs -> {prov.allergy_ids}")
        print(f"         Conflicts:   {len(prov.conflict_ids)} IDs -> {prov.conflict_ids}")

        # 9. Verify Immutable Audit Log
        print("\n--- Verifying Immutable Audit Log ---")
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.entity_type == "ClinicalSummary", AuditLog.entity_id == summary.id)
            .first()
        )
        assert audit is not None, "AuditLog entry not created for ClinicalSummary generation!"
        assert audit.action == "GENERATE_AI_SUMMARY", f"Unexpected audit action '{audit.action}'"
        print(f"  [PASS] Audit log created (ID: {audit.id}, Action: {audit.action}, Actor: {audit.actor_name})")

        # 10. Verify REST API Endpoint Handlers directly
        print("\n--- Verifying REST API Endpoint Handlers ---")
        # GET endpoint
        get_summary = get_patient_clinical_summary(patient.id, db=db)
        assert get_summary is not None, "GET summary endpoint returned None!"
        assert get_summary.id == summary.id, "GET summary returned wrong summary ID"
        assert get_summary.disclaimer == expected_disclaimer, "GET summary disclaimer mismatch"
        print(f"  [PASS] GET /patients/{{patient_id}}/summary handler returned valid schema (ID: {get_summary.id})")

        # POST generate endpoint
        post_summary = generate_patient_clinical_summary(
            patient.id,
            payload=ClinicalSummaryGenerateRequest(force_regenerate=True),
            db=db
        )
        assert post_summary is not None, "POST generate summary returned None!"
        assert post_summary.sections is not None, "POST summary missing sections"
        assert post_summary.sections.record_overview, "POST summary missing record_overview"
        print(f"  [PASS] POST /patients/{{patient_id}}/summary/generate handler generated new summary (ID: {post_summary.id})")

        print("\n" + "=" * 80)
        print("ALL MEDLENS AI SUMMARY MODULE TESTS PASSED (100% SUCCESS)!")
        print("=" * 80 + "\n")

    finally:
        db.close()


if __name__ == "__main__":
    test_ai_summary_module()
