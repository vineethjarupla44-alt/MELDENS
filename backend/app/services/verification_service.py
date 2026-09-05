import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.models import (
    Patient,
    LabResult,
    Medication,
    Condition,
    Allergy,
    Observation,
    ConflictRecord,
    VerificationRecord,
    AuditLog,
    VerificationStatusEnum,
    LabStatusEnum,
)
from app.schemas.verification import (
    VerificationQueueItem,
    VerificationActionRequest,
    VerificationActionResponse,
)

class VerificationService:
    def __init__(self, db: Session):
        self.db = db

    def get_verification_queue(self, patient_id: Optional[str] = None) -> List[VerificationQueueItem]:
        """
        Aggregates clinical items requiring human review:
        - Low extraction confidence (< 90%)
        - Ambiguity (e.g. UNKNOWN status, missing reference range, or unparsed text)
        - Conflicting documentation (linked to unresolved ConflictRecord)
        - Manual confirmation required (UNVERIFIED)
        """
        queue_items: List[VerificationQueueItem] = []

        # Load patients map for patient names
        patients = {p.id: f"{p.first_name} {p.last_name}" for p in self.db.query(Patient).all()}

        # Load active unresolved conflicts for matching
        conflicts_query = self.db.query(ConflictRecord).filter(ConflictRecord.status == "UNRESOLVED")
        if patient_id:
            conflicts_query = conflicts_query.filter(ConflictRecord.patient_id == patient_id)
        active_conflicts = conflicts_query.all()
        conflict_field_map = {(c.patient_id, c.field_name.lower()): c.description for c in active_conflicts}

        # 1. Process Lab Results
        lab_query = self.db.query(LabResult)
        if patient_id:
            lab_query = lab_query.filter(LabResult.patient_id == patient_id)
        labs = lab_query.all()

        for lab in labs:
            reasons = []
            if lab.confidence is not None and lab.confidence < 0.90:
                reasons.append(f"Low Confidence ({int(lab.confidence * 100)}%)")
            if lab.status == LabStatusEnum.UNKNOWN or (lab.reference_range_low is None and lab.reference_range_high is None):
                reasons.append("Reference Range Not Provided (Ambiguity)")
            if (lab.patient_id, lab.test_name.lower()) in conflict_field_map:
                reasons.append(f"Conflicting Documentation: {conflict_field_map[(lab.patient_id, lab.test_name.lower())]}")
            if lab.verification_status == VerificationStatusEnum.UNVERIFIED:
                reasons.append("Manual Confirmation Required")

            if reasons or lab.verification_status == VerificationStatusEnum.UNVERIFIED:
                extracted_str = f"{lab.value} {lab.unit or ''}".strip() if lab.value is not None else (lab.raw_value or "Unparsed")
                orig_val = lab.raw_value or str(lab.value or "")
                queue_items.append(
                    VerificationQueueItem(
                        id=lab.id,
                        entity_type="lab",
                        patient_id=lab.patient_id,
                        patient_name=patients.get(lab.patient_id, "Unknown Patient"),
                        item_name=lab.test_name,
                        extracted_value=extracted_str,
                        original_value=orig_val,
                        editable_value=lab.corrected_value or orig_val,
                        corrected_value=lab.corrected_value,
                        source_document=lab.source_document,
                        page_number=lab.source_page,
                        confidence=lab.confidence,
                        reasons=reasons,
                        verification_status=lab.verification_status.value if lab.verification_status else "UNVERIFIED",
                        verified_by=lab.verified_by,
                        verified_at=lab.verified_at,
                        source_snippet=lab.source_snippet,
                        document_id=lab.document_id,
                        created_at=lab.created_at or datetime.utcnow(),
                    )
                )

        # 2. Process Medications
        med_query = self.db.query(Medication)
        if patient_id:
            med_query = med_query.filter(Medication.patient_id == patient_id)
        meds = med_query.all()

        for med in meds:
            reasons = []
            if med.confidence is not None and med.confidence < 0.90:
                reasons.append(f"Low Confidence ({int(med.confidence * 100)}%)")
            if (med.patient_id, med.medication_name.lower()) in conflict_field_map or (med.patient_id, "medication") in conflict_field_map:
                reasons.append("Conflicting Medication Schedule Across Records")
            if med.verification_status == VerificationStatusEnum.UNVERIFIED:
                reasons.append("Manual Confirmation Required")

            if reasons or med.verification_status == VerificationStatusEnum.UNVERIFIED:
                parts = [p for p in [med.dosage, med.frequency, f"({med.route})" if med.route else ""] if p]
                ext_str = f"{med.medication_name}: " + (" · ".join(parts) if parts else "Documented")
                orig_val = med.raw_text or med.dosage or med.medication_name
                queue_items.append(
                    VerificationQueueItem(
                        id=med.id,
                        entity_type="medication",
                        patient_id=med.patient_id,
                        patient_name=patients.get(med.patient_id, "Unknown Patient"),
                        item_name=med.medication_name,
                        extracted_value=ext_str,
                        original_value=orig_val,
                        editable_value=med.corrected_value or orig_val,
                        corrected_value=med.corrected_value,
                        source_document=med.source_document,
                        page_number=med.source_page,
                        confidence=med.confidence,
                        reasons=reasons,
                        verification_status=med.verification_status.value if med.verification_status else "UNVERIFIED",
                        verified_by=med.verified_by,
                        verified_at=med.verified_at,
                        source_snippet=med.source_snippet,
                        document_id=med.document_id,
                        created_at=med.created_at or datetime.utcnow(),
                    )
                )

        # 3. Process Conditions
        cond_query = self.db.query(Condition)
        if patient_id:
            cond_query = cond_query.filter(Condition.patient_id == patient_id)
        conditions = cond_query.all()

        for cond in conditions:
            reasons = []
            if cond.confidence is not None and cond.confidence < 0.90:
                reasons.append(f"Low Confidence ({int(cond.confidence * 100)}%)")
            if (cond.patient_id, cond.condition_name.lower()) in conflict_field_map:
                reasons.append("Conflicting Diagnostic Documentation")
            if cond.verification_status == VerificationStatusEnum.UNVERIFIED:
                reasons.append("Manual Confirmation Required")

            if reasons or cond.verification_status == VerificationStatusEnum.UNVERIFIED:
                ext_str = cond.condition_name + (f" (ICD-10: {cond.icd10_code})" if cond.icd10_code else "")
                orig_val = cond.raw_text or cond.condition_name
                queue_items.append(
                    VerificationQueueItem(
                        id=cond.id,
                        entity_type="condition",
                        patient_id=cond.patient_id,
                        patient_name=patients.get(cond.patient_id, "Unknown Patient"),
                        item_name=cond.condition_name,
                        extracted_value=ext_str,
                        original_value=orig_val,
                        editable_value=cond.corrected_value or orig_val,
                        corrected_value=cond.corrected_value,
                        source_document=cond.source_document,
                        page_number=cond.source_page,
                        confidence=cond.confidence,
                        reasons=reasons,
                        verification_status=cond.verification_status.value if cond.verification_status else "UNVERIFIED",
                        verified_by=cond.verified_by,
                        verified_at=cond.verified_at,
                        source_snippet=cond.source_snippet,
                        document_id=cond.document_id,
                        created_at=cond.created_at or datetime.utcnow(),
                    )
                )

        # 4. Process Allergies
        alg_query = self.db.query(Allergy)
        if patient_id:
            alg_query = alg_query.filter(Allergy.patient_id == patient_id)
        allergies = alg_query.all()

        for alg in allergies:
            reasons = []
            if alg.confidence is not None and alg.confidence < 0.90:
                reasons.append(f"Low Confidence ({int(alg.confidence * 100)}%)")
            if (alg.patient_id, alg.allergen.lower()) in conflict_field_map or (alg.patient_id, "allergy") in conflict_field_map:
                reasons.append(f"Conflicting Allergen Records: {conflict_field_map.get((alg.patient_id, alg.allergen.lower())) or conflict_field_map.get((alg.patient_id, 'allergy'))}")
            if alg.verification_status == VerificationStatusEnum.UNVERIFIED:
                reasons.append("Manual Confirmation Required")

            if reasons or alg.verification_status == VerificationStatusEnum.UNVERIFIED:
                parts = [p for p in [alg.reaction, f"Severity: {alg.severity}" if alg.severity else ""] if p]
                ext_str = f"{alg.allergen} — " + (" · ".join(parts) if parts else "Documented")
                orig_val = alg.raw_text or alg.allergen
                queue_items.append(
                    VerificationQueueItem(
                        id=alg.id,
                        entity_type="allergy",
                        patient_id=alg.patient_id,
                        patient_name=patients.get(alg.patient_id, "Unknown Patient"),
                        item_name=alg.allergen,
                        extracted_value=ext_str,
                        original_value=orig_val,
                        editable_value=alg.corrected_value or orig_val,
                        corrected_value=alg.corrected_value,
                        source_document=alg.source_document,
                        page_number=alg.source_page,
                        confidence=alg.confidence,
                        reasons=reasons,
                        verification_status=alg.verification_status.value if alg.verification_status else "UNVERIFIED",
                        verified_by=alg.verified_by,
                        verified_at=alg.verified_at,
                        source_snippet=alg.source_snippet,
                        document_id=alg.document_id,
                        created_at=alg.created_at or datetime.utcnow(),
                    )
                )

        # 5. Process Observations
        obs_query = self.db.query(Observation)
        if patient_id:
            obs_query = obs_query.filter(Observation.patient_id == patient_id)
        observations = obs_query.all()

        for obs in observations:
            reasons = []
            if obs.confidence is not None and obs.confidence < 0.90:
                reasons.append(f"Low Confidence ({int(obs.confidence * 100)}%)")
            if obs.verification_status == VerificationStatusEnum.UNVERIFIED:
                reasons.append("Manual Confirmation Required")

            if reasons or obs.verification_status == VerificationStatusEnum.UNVERIFIED:
                ext_str = f"{obs.numeric_value or obs.string_value or ''} {obs.unit or ''}".strip()
                orig_val = obs.string_value or (str(obs.numeric_value) if obs.numeric_value is not None else "Observed")
                queue_items.append(
                    VerificationQueueItem(
                        id=obs.id,
                        entity_type="observation",
                        patient_id=obs.patient_id,
                        patient_name=patients.get(obs.patient_id, "Unknown Patient"),
                        item_name=obs.observation_name or obs.observation_type,
                        extracted_value=ext_str,
                        original_value=orig_val,
                        editable_value=obs.corrected_value or orig_val,
                        corrected_value=obs.corrected_value,
                        source_document=obs.source_document,
                        page_number=obs.source_page,
                        confidence=obs.confidence,
                        reasons=reasons,
                        verification_status=obs.verification_status.value if obs.verification_status else "UNVERIFIED",
                        verified_by=obs.verified_by,
                        verified_at=obs.verified_at,
                        source_snippet=obs.source_snippet,
                        document_id=obs.document_id,
                        created_at=obs.created_at or datetime.utcnow(),
                    )
                )

        # Sort: items with conflicts and low confidence first, then pending, then verified
        def sort_priority(item: VerificationQueueItem):
            is_pending = item.verification_status == "UNVERIFIED"
            has_conflict = any("Conflict" in r for r in item.reasons)
            has_low_conf = any("Low Confidence" in r for r in item.reasons)
            return (not is_pending, not has_conflict, not has_low_conf)

        queue_items.sort(key=sort_priority)
        return queue_items

    def execute_verification_action(self, payload: VerificationActionRequest) -> VerificationActionResponse:
        """
        Executes human clinician verification action: ACCEPT, EDIT, or REJECT.
        Strictly obeys clinical non-diagnostic rules:
        - Never deletes original AI extraction.
        - Preserves raw_value/raw_text as immutable ground truth.
        - Stores corrected_value, verifier, and timestamp when edited.
        - Records signed VerificationRecord and immutable AuditLog entry.
        """
        etype = payload.entity_type.lower()
        model_map = {
            "lab": LabResult,
            "medication": Medication,
            "condition": Condition,
            "allergy": Allergy,
            "observation": Observation,
        }

        model = model_map.get(etype)
        if not model:
            raise HTTPException(status_code=400, detail=f"Invalid entity type '{payload.entity_type}'")

        item = self.db.query(model).filter(model.id == payload.entity_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Clinical entity not found")

        # Ground truth original value (NEVER deleted or modified)
        original_val = (
            getattr(item, "raw_value", None)
            or getattr(item, "raw_text", None)
            or getattr(item, "dosage", None)
            or getattr(item, "medication_name", None)
            or getattr(item, "condition_name", None)
            or getattr(item, "allergen", None)
            or str(getattr(item, "value", "") or "")
        )

        action_clean = payload.action.upper()
        now = datetime.utcnow()

        if action_clean == "ACCEPT":
            new_status = VerificationStatusEnum.VERIFIED
            corrected_val = getattr(item, "corrected_value", None)
            change_note = payload.notes or "Clinician confirmed AI extraction as clinically accurate"
            audit_action = "HUMAN_VERIFY_ACCEPT"

        elif action_clean == "EDIT":
            new_status = VerificationStatusEnum.VERIFIED
            corrected_val = payload.corrected_value
            if not corrected_val:
                raise HTTPException(status_code=400, detail="Edited value cannot be empty")
            item.corrected_value = corrected_val
            
            # If lab, update numeric parsed value if numeric
            if etype == "lab":
                try:
                    num_val = float(corrected_val.split()[0].replace(",", "."))
                    item.value = num_val
                except (ValueError, IndexError):
                    pass

            change_note = payload.notes or f"Clinician corrected value from '{original_val}' to '{corrected_val}'"
            audit_action = "HUMAN_VERIFY_EDIT"

        elif action_clean == "REJECT":
            new_status = VerificationStatusEnum.REJECTED
            corrected_val = getattr(item, "corrected_value", None)
            change_note = payload.notes or "Clinician rejected extracted data as artifact/inaccurate"
            audit_action = "HUMAN_VERIFY_REJECT"

        else:
            raise HTTPException(status_code=400, detail=f"Invalid action '{payload.action}'. Expected ACCEPT, EDIT, or REJECT.")

        # Update entity verification metadata
        item.verification_status = new_status
        item.verified_by = payload.reviewer_name
        item.verified_at = now

        # Create signed VerificationRecord
        verification_record = VerificationRecord(
            id=str(uuid.uuid4()),
            entity_type=model.__name__,
            entity_id=item.id,
            reviewer_id=payload.reviewer_id,
            reviewer_name=payload.reviewer_name,
            reviewer_role=payload.reviewer_role,
            action=action_clean,
            original_value=original_val,
            corrected_value=corrected_val,
            status=new_status,
            notes=change_note,
            signed_at=now,
        )
        self.db.add(verification_record)

        # Create immutable AuditLog
        audit = AuditLog(
            id=str(uuid.uuid4()),
            entity_type=model.__name__,
            entity_id=item.id,
            action=audit_action,
            actor_id=payload.reviewer_id,
            actor_name=payload.reviewer_name,
            previous_state=str(original_val),
            new_state=str(corrected_val or new_status.value),
            change_reason=change_note,
            timestamp=now,
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(item)

        return VerificationActionResponse(
            status="success",
            entity_type=etype,
            entity_id=item.id,
            action=action_clean,
            original_value=original_val,
            corrected_value=corrected_val,
            verification_status=new_status.value,
            verified_by=payload.reviewer_name,
            verified_at=now,
            audit_id=audit.id,
        )
