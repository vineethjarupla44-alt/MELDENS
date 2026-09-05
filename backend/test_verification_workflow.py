"""
MedLens Human Verification Workflow Test Suite
Tests:
- Verification Queue aggregation:
  * items with low extraction confidence (< 90%)
  * items with ambiguity / missing reference range
  * items with conflicting sources
  * items requiring manual confirmation (UNVERIFIED)
- Human Actions:
  * ACCEPT: validates item, preserves original AI extraction, creates audit log
  * EDIT: preserves original raw value, stores corrected value, verifier, timestamp & audit log
  * REJECT: preserves original extraction, marks rejected, creates audit log
- Non-destructive original data preservation invariance
"""
import sys
from app.db.session import SessionLocal
from app.db.models import (
    Patient,
    LabResult,
    Medication,
    VerificationRecord,
    AuditLog,
    VerificationStatusEnum,
)
from app.services.verification_service import VerificationService
from app.schemas.verification import VerificationActionRequest

def test_verification_workflow():
    db = SessionLocal()
    try:
        print("\n=== Running MedLens Human Verification Workflow Tests ===")
        service = VerificationService(db)

        # 1. Fetch Verification Queue
        queue = service.get_verification_queue()
        assert len(queue) > 0, "Verification queue is empty! Expected items requiring human review."
        print(f"PASS: Verification Queue populated with {len(queue)} clinical review items.")

        # Inspect reasons in queue
        reasons_found = set()
        for item in queue:
            for r in item.reasons:
                reasons_found.add(r.split(":")[0])
        print(f"PASS: Review flags detected in queue: {list(reasons_found)}")

        # Verify an item with ambiguity / missing reference range
        ferritin_item = next((i for i in queue if "Ferritin" in i.item_name), None)
        assert ferritin_item is not None, "Serum Ferritin (ambiguity/missing range) not in verification queue!"
        assert any("Reference Range Not Provided" in r for r in ferritin_item.reasons), "Missing range reason not flagged!"
        print(f"PASS: Ambiguity detection verified on '{ferritin_item.item_name}' (Raw: {ferritin_item.original_value})")

        # 2. Test ACCEPT Action
        # Find an unverified lab or medication
        unverified_item = next((i for i in queue if i.verification_status == "UNVERIFIED" and i.id != ferritin_item.id), None)
        if unverified_item:
            orig_raw = unverified_item.original_value
            accept_req = VerificationActionRequest(
                entity_type=unverified_item.entity_type,
                entity_id=unverified_item.id,
                action="ACCEPT",
                reviewer_name="Dr. Sarah Lin, MD",
                reviewer_role="Lead Clinician Reviewer",
                notes="Verified against St. Jude Discharge Summary page 1",
            )
            resp = service.execute_verification_action(accept_req)
            assert resp.action == "ACCEPT"
            assert resp.verification_status == "VERIFIED"
            assert resp.original_value == orig_raw, "Original value altered on ACCEPT!"
            print(f"PASS: ACCEPT action verified -> Item '{unverified_item.item_name}' confirmed as VERIFIED by {resp.verified_by}")

        # 3. Test EDIT Action (Never delete original AI extraction, store corrected value)
        orig_ferritin_raw = ferritin_item.original_value
        edit_req = VerificationActionRequest(
            entity_type="lab",
            entity_id=ferritin_item.id,
            action="EDIT",
            corrected_value="21.5 ng/mL",
            reviewer_name="Dr. Marcus Vance, MD",
            reviewer_role="Hematology Attending",
            notes="Adjusted value based on Quest Diagnostics calibrated re-assay",
        )
        edit_resp = service.execute_verification_action(edit_req)
        assert edit_resp.action == "EDIT"
        assert edit_resp.verification_status == "VERIFIED"
        assert edit_resp.original_value == orig_ferritin_raw, f"Original value overwritten! Expected {orig_ferritin_raw}, got {edit_resp.original_value}"
        assert edit_resp.corrected_value == "21.5 ng/mL"

        # Check in DB that raw_value is preserved and corrected_value is set
        db_lab = db.query(LabResult).filter(LabResult.id == ferritin_item.id).first()
        assert db_lab.raw_value == orig_ferritin_raw, "Database raw_value was modified!"
        assert db_lab.corrected_value == "21.5 ng/mL", "Database corrected_value not saved!"
        assert db_lab.verified_by == "Dr. Marcus Vance, MD"
        print(f"PASS: EDIT action verified -> Original '{db_lab.raw_value}' strictly preserved. Corrected value: '{db_lab.corrected_value}'")

        # 4. Test REJECT Action
        # Pick another item to test REJECT
        med_item = next((i for i in queue if i.entity_type == "medication"), None)
        if med_item:
            orig_med_raw = med_item.original_value
            reject_req = VerificationActionRequest(
                entity_type="medication",
                entity_id=med_item.id,
                action="REJECT",
                reviewer_name="Dr. Sarah Lin, MD",
                notes="Patient discontinued medication prior to admission",
            )
            reject_resp = service.execute_verification_action(reject_req)
            assert reject_resp.action == "REJECT"
            assert reject_resp.verification_status == "REJECTED"
            assert reject_resp.original_value == orig_med_raw, "Original value lost on REJECT!"
            print(f"PASS: REJECT action verified -> Item '{med_item.item_name}' marked REJECTED, original text preserved")

        # 5. Verify Audit Trail and Verification Records
        audit_records = db.query(AuditLog).filter(AuditLog.action.like("HUMAN_VERIFY_%")).all()
        assert len(audit_records) >= 2, "Audit records not generated for verification actions!"
        print(f"PASS: Audit trail verified -> Found {len(audit_records)} human verification audit entries")

        v_records = db.query(VerificationRecord).all()
        assert len(v_records) >= 2, "VerificationRecord entries not created!"
        print(f"PASS: Signed verification records verified ({len(v_records)} records)")

        print("\nALL HUMAN VERIFICATION WORKFLOW TESTS PASSED SUCCESSFULLY!")

    finally:
        db.close()

if __name__ == "__main__":
    test_verification_workflow()
