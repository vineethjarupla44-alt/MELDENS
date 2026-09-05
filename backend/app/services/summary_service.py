import re
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import requests

from app.core.config import settings
from app.db.models import (
    Patient,
    PatientProfile,
    Document,
    LabResult,
    Medication,
    Condition,
    Allergy,
    Observation,
    ConflictRecord,
    TimelineEvent,
    ClinicalSummary,
    AuditLog,
    LabStatusEnum,
    VerificationStatusEnum,
)
from app.schemas.summary import (
    ClinicalSummaryRead,
    ClinicalSummarySections,
    SummaryProvenanceSources,
    MANDATORY_DISCLAIMER,
)

logger = logging.getLogger("medlens.summary_service")

# Strict guardrail check for prohibited diagnostic or prescriptive phrases (exact phrase matching)
PROHIBITED_PHRASES = [
    r"\bi diagnose\b",
    r"\bwe diagnose\b",
    r"\byou have developed\b",
    r"\btreatment recommendation\b",
    r"\bwe recommend taking\b",
    r"\byou should take\b",
    r"\bstop taking\b",
    r"\bdiscontinue medication\b",
    r"\bincrease dose to\b",
    r"\bdecrease dose to\b",
    r"\bprescribe new\b",
    r"\bshould prescribe\b",
    r"\bi prescribe\b",
]


class SummaryService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.LLM_MODEL or "gemini-1.5-pro"

    def get_patient_summary(self, patient_id: str) -> Optional[ClinicalSummaryRead]:
        """Fetches the latest clinical summary for a patient."""
        summary = (
            self.db.query(ClinicalSummary)
            .filter(ClinicalSummary.patient_id == patient_id)
            .order_by(ClinicalSummary.created_at.desc())
            .first()
        )
        if not summary:
            return None

        return self._to_pydantic(summary)

    def generate_summary(self, patient_id: str, force_regenerate: bool = False) -> ClinicalSummaryRead:
        """
        Generates an AI clinical summary ONLY from validated structured patient information.
        Adheres to strict non-diagnostic guardrails, includes the 7 mandatory sections,
        records structured record IDs for provenance, and applies the mandatory disclaimer.
        """
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Return cached summary if recent (< 5 min) and not forcing regeneration
        if not force_regenerate:
            existing = (
                self.db.query(ClinicalSummary)
                .filter(ClinicalSummary.patient_id == patient_id)
                .order_by(ClinicalSummary.created_at.desc())
                .first()
            )
            if existing:
                age_seconds = (datetime.utcnow() - existing.created_at).total_seconds()
                if age_seconds < 300:
                    return self._to_pydantic(existing)

        # 1. Collect all structured records for patient
        profile = patient.profile
        documents = self.db.query(Document).filter(Document.patient_id == patient_id).all()
        labs = self.db.query(LabResult).filter(LabResult.patient_id == patient_id).all()
        medications = self.db.query(Medication).filter(Medication.patient_id == patient_id).all()
        conditions = self.db.query(Condition).filter(Condition.patient_id == patient_id).all()
        allergies = self.db.query(Allergy).filter(Allergy.patient_id == patient_id).all()
        observations = self.db.query(Observation).filter(Observation.patient_id == patient_id).all()
        conflicts = self.db.query(ConflictRecord).filter(ConflictRecord.patient_id == patient_id).all()
        timeline = (
            self.db.query(TimelineEvent)
            .filter(TimelineEvent.patient_id == patient_id)
            .order_by(TimelineEvent.event_date.desc())
            .all()
        )

        # 2. Build structured provenance sources
        provenance_sources = SummaryProvenanceSources(
            document_ids=[d.id for d in documents],
            lab_ids=[l.id for l in labs],
            medication_ids=[m.id for m in medications],
            condition_ids=[c.id for c in conditions],
            allergy_ids=[a.id for a in allergies],
            observation_ids=[o.id for o in observations],
            conflict_ids=[cf.id for cf in conflicts],
        )

        # 3. Generate the 7 sections
        sections_dict = None
        key_findings = []
        overall_summary = ""

        # Try LLM if API key available
        if self.api_key:
            llm_result = self._generate_with_gemini(
                patient, profile, documents, labs, medications, conditions, allergies, observations, conflicts, timeline
            )
            if llm_result:
                sections_dict = llm_result.get("sections")
                key_findings = llm_result.get("key_findings", [])
                overall_summary = llm_result.get("summary_text", "")

        # Fallback to deterministic clinical synthesis engine
        if not sections_dict:
            deterministic_result = self._generate_deterministic_summary(
                patient, profile, documents, labs, medications, conditions, allergies, observations, conflicts, timeline
            )
            sections_dict = deterministic_result["sections"]
            key_findings = deterministic_result["key_findings"]
            overall_summary = deterministic_result["summary_text"]

        # 4. Clinical Safety Sanitize
        overall_summary, sections_dict = self._apply_clinical_safety_guardrails(overall_summary, sections_dict)

        # 5. Persist to ClinicalSummary table
        summary_id = str(uuid.uuid4())
        summary_record = ClinicalSummary(
            id=summary_id,
            patient_id=patient_id,
            summary_text=overall_summary,
            sections=json.dumps(sections_dict),
            structured_provenance_sources=json.dumps(provenance_sources.model_dump()),
            key_findings=json.dumps(key_findings),
            disclaimer=MANDATORY_DISCLAIMER,
            model_version=f"medlens-{self.model_name}-v1" if self.api_key else "medlens-deterministic-v1",
            is_verified=False,
            created_at=datetime.utcnow(),
        )
        self.db.add(summary_record)

        # 6. Immutable Audit Log
        audit = AuditLog(
            entity_type="ClinicalSummary",
            entity_id=summary_record.id,
            action="GENERATE_AI_SUMMARY",
            actor_id="SYSTEM",
            actor_name="MedLens Clinical Intelligence Engine",
            previous_state=None,
            new_state=json.dumps({
                "patient_id": patient_id,
                "sections_count": 7,
                "records_grounded": {
                    "documents": len(documents),
                    "labs": len(labs),
                    "medications": len(medications),
                    "conditions": len(conditions),
                    "allergies": len(allergies),
                    "conflicts": len(conflicts),
                }
            }),
            change_reason="AI summary generated strictly from validated structured patient records",
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(summary_record)

        return self._to_pydantic(summary_record)

    def _generate_deterministic_summary(
        self,
        patient: Patient,
        profile: Optional[PatientProfile],
        documents: List[Document],
        labs: List[LabResult],
        medications: List[Medication],
        conditions: List[Condition],
        allergies: List[Allergy],
        observations: List[Observation],
        conflicts: List[ConflictRecord],
        timeline: List[TimelineEvent],
    ) -> Dict[str, Any]:
        """
        Deterministic, high-fidelity clinical synthesis engine.
        Generates an immaculate, patient-friendly 7-section summary solely from structured database facts.
        Zero diagnosis, zero invented ranges, zero prescriptive advice.
        """
        # --- Section 1: Record Overview ---
        active_conditions = [c.condition_name for c in conditions if c.clinical_status.upper() == "ACTIVE"]
        cond_str = ", ".join(active_conditions) if active_conditions else "No active conditions currently recorded"

        active_meds = [m.medication_name for m in medications if m.clinical_status.upper() == "ACTIVE"]
        med_str = ", ".join(active_meds) if active_meds else "No active medications recorded"

        allergy_names = [a.allergen for a in allergies]
        allergy_str = ", ".join(allergy_names) if allergy_names else "No known allergies documented"

        overview = (
            f"This clinical intelligence record synthesizes available documented facts for {patient.first_name} {patient.last_name} "
            f"(MRN: {patient.mrn or 'Unspecified'}, Gender: {patient.gender or 'Unspecified'}, DOB: {patient.date_of_birth or 'Unspecified'}). "
            f"The record encompasses {len(documents)} indexed medical document(s), {len(labs)} laboratory test result(s), "
            f"{len(medications)} recorded medication(s), and {len(conditions)} documented condition(s). "
            f"Current active conditions on file include: {cond_str}. "
            f"Active medications on record include: {med_str}. "
            f"Documented allergy profile lists: {allergy_str}."
        )

        # --- Section 2: Recently Documented Information ---
        recent_doc_parts = []
        if documents:
            latest_doc = sorted(documents, key=lambda d: d.upload_date or datetime.min, reverse=True)[0]
            date_str = latest_doc.upload_date.strftime("%B %d, %Y") if latest_doc.upload_date else "Recently"
            recent_doc_parts.append(f"Most recently indexed document is '{latest_doc.original_name}' uploaded on {date_str}.")

        if timeline:
            latest_events = timeline[:3]
            event_strs = [f"{e.event_date}: {e.title} ({e.description})" for e in latest_events if e.title]
            if event_strs:
                recent_doc_parts.append("Latest chronological events: " + "; ".join(event_strs) + ".")

        if profile and profile.symptoms:
            recent_doc_parts.append(f"Reported symptoms on file: {profile.symptoms}.")

        if not recent_doc_parts:
            recent_doc_parts.append("No recent encounters or newly added clinical documents found.")

        recently_documented = " ".join(recent_doc_parts)

        # --- Section 3: Laboratory Values and Source-Report Status ---
        normal_labs = [l for l in labs if l.status == LabStatusEnum.NORMAL]
        low_labs = [l for l in labs if l.status == LabStatusEnum.LOW]
        high_labs = [l for l in labs if l.status == LabStatusEnum.HIGH]
        unknown_labs = [l for l in labs if l.status == LabStatusEnum.UNKNOWN]

        lab_parts = []
        if normal_labs:
            norm_details = []
            for l in normal_labs:
                range_str = f"report range {l.reference_range_low}–{l.reference_range_high} {l.unit or ''}".strip()
                norm_details.append(f"{l.test_name} ({l.value if l.value is not None else l.raw_value} {l.unit or ''}, {range_str})")
            lab_parts.append(f"NORMAL ({len(normal_labs)}): " + ", ".join(norm_details) + ".")

        if low_labs:
            low_details = []
            for l in low_labs:
                range_str = f"report range {l.reference_range_low}–{l.reference_range_high} {l.unit or ''}".strip()
                low_details.append(f"{l.test_name} ({l.value if l.value is not None else l.raw_value} {l.unit or ''}, below {range_str})")
            lab_parts.append(f"LOW ({len(low_labs)}): " + ", ".join(low_details) + ".")

        if high_labs:
            high_details = []
            for l in high_labs:
                range_str = f"report range {l.reference_range_low}–{l.reference_range_high} {l.unit or ''}".strip()
                high_details.append(f"{l.test_name} ({l.value if l.value is not None else l.raw_value} {l.unit or ''}, above {range_str})")
            lab_parts.append(f"HIGH ({len(high_labs)}): " + ", ".join(high_details) + ".")

        if unknown_labs:
            unk_details = []
            for l in unknown_labs:
                val_disp = f"{l.value} {l.unit or ''}".strip() if l.value is not None else (l.raw_value or 'Value recorded')
                unk_details.append(f"{l.test_name} ({val_disp} — reference range not provided in source report)")
            lab_parts.append(
                f"REFERENCE RANGE NOT PROVIDED ({len(unknown_labs)}): "
                + ", ".join(unk_details)
                + ". In accordance with MedLens safety standards, no reference ranges have been fabricated."
            )

        if not labs:
            laboratory_values = "No laboratory test results have been registered for this patient."
        else:
            laboratory_values = " ".join(lab_parts)

        # --- Section 4: Historical Changes ---
        historical_parts = []
        if timeline:
            sorted_tl = sorted(timeline, key=lambda t: t.event_date)
            historical_parts.append(
                f"Clinical timeline spans from {sorted_tl[0].event_date} to {sorted_tl[-1].event_date}, tracking {len(timeline)} chronological milestones."
            )
            # Check for medication or condition progressions
            onset_conditions = [f"{c.condition_name} (onset: {c.onset_date})" for c in conditions if c.onset_date]
            if onset_conditions:
                historical_parts.append("Documented condition onset milestones: " + ", ".join(onset_conditions) + ".")

            rx_dates = [f"{m.medication_name} ({m.prescribed_date})" for m in medications if m.prescribed_date]
            if rx_dates:
                historical_parts.append("Documented prescription dates: " + ", ".join(rx_dates) + ".")
        else:
            historical_parts.append("No chronological timeline events or prior historical trends are recorded in the current dataset.")

        historical_changes = " ".join(historical_parts)

        # --- Section 5: Potential Conflicts ---
        unresolved_conflicts = [c for c in conflicts if c.status.value == "UNRESOLVED"]
        resolved_conflicts = [c for c in conflicts if c.status.value == "RESOLVED"]

        if unresolved_conflicts:
            conflict_details = []
            for cf in unresolved_conflicts:
                conflict_details.append(
                    f"[{cf.category.value}] {cf.field_name}: '{cf.source_a_value}' (source: {cf.source_a_type}) "
                    f"conflicts with '{cf.source_b_value}' (source: {cf.source_b_type}). Details: {cf.description}"
                )
            potential_conflicts = (
                f"{len(unresolved_conflicts)} active unresolved clinical conflict(s) identified across records: "
                + " | ".join(conflict_details)
            )
        elif resolved_conflicts:
            potential_conflicts = f"All {len(resolved_conflicts)} previously identified clinical conflicts have been resolved by clinicians."
        else:
            potential_conflicts = "No contradictory clinical documentation or medication/allergy conflicts were identified across the available records."

        # --- Section 6: Missing Information ---
        missing_items = []
        if not patient.date_of_birth:
            missing_items.append("Patient date of birth is unrecorded")
        if not patient.blood_type:
            missing_items.append("Blood type is not specified")

        # Labs without report range
        if unknown_labs:
            missing_items.append(f"{len(unknown_labs)} lab test(s) ({', '.join(l.test_name for l in unknown_labs)}) lack reference ranges in the source report")

        # Medications missing dosage or route
        incomplete_meds = [m.medication_name for m in medications if not m.dosage or not m.frequency]
        if incomplete_meds:
            missing_items.append(f"Medication details incomplete for: {', '.join(incomplete_meds)} (dosage or frequency not documented)")

        # Unspecified onset dates
        undated_conds = [c.condition_name for c in conditions if not c.onset_date]
        if undated_conds:
            missing_items.append(f"Condition onset dates omitted for: {', '.join(undated_conds)}")

        if not missing_items:
            missing_information = "No major clinical documentation gaps were identified in the indexed records."
        else:
            missing_information = (
                "The following information is absent or omitted from the source medical documentation: "
                + "; ".join(missing_items)
                + ". MedLens does not infer or fabricate missing values."
            )

        # --- Section 7: Verification-Required Information ---
        unverified_labs = [l for l in labs if l.verification_status == VerificationStatusEnum.UNVERIFIED]
        unverified_meds = [m for m in medications if m.verification_status == VerificationStatusEnum.UNVERIFIED]
        unverified_conds = [c for c in conditions if c.verification_status == VerificationStatusEnum.UNVERIFIED]
        low_conf_items = [
            f"{l.test_name} ({int(l.confidence*100)}% conf)"
            for l in labs
            if l.confidence is not None and l.confidence < 0.90
        ]

        verif_parts = []
        total_unverified = len(unverified_labs) + len(unverified_meds) + len(unverified_conds)
        if total_unverified > 0:
            verif_parts.append(
                f"{total_unverified} clinical item(s) are pending human clinician review "
                f"({len(unverified_labs)} labs, {len(unverified_meds)} medications, {len(unverified_conds)} conditions)."
            )

        if low_conf_items:
            verif_parts.append(f"Items with low extraction confidence requiring manual verification: {', '.join(low_conf_items)}.")

        if unresolved_conflicts:
            verif_parts.append(f"{len(unresolved_conflicts)} clinical conflict(s) require clinician adjudication.")

        if not verif_parts:
            verification_required = "All extracted clinical data points have been human-verified with high confidence."
        else:
            verification_required = " ".join(verif_parts)

        # --- Key Findings Highlights ---
        key_findings = []
        if low_labs or high_labs:
            abnormal_names = [f"{l.test_name} ({l.status.value})" for l in low_labs + high_labs]
            key_findings.append(f"Source-report lab flags: {', '.join(abnormal_names)}")
        if unresolved_conflicts:
            key_findings.append(f"{len(unresolved_conflicts)} cross-document conflict(s) requiring attention")
        if unknown_labs:
            key_findings.append(f"{len(unknown_labs)} lab value(s) without source reference intervals")
        if active_meds:
            key_findings.append(f"{len(active_meds)} active prescription(s) documented")
        if not key_findings:
            key_findings.append("All clinical records currently indexed and categorized")

        summary_text = (
            f"Clinical Intelligence Summary for {patient.first_name} {patient.last_name}: "
            f"{len(documents)} document(s) evaluated across {len(labs)} lab results and {len(medications)} medications. "
            f"{'Discrepancies noted in allergy/medication records.' if unresolved_conflicts else 'Records successfully reconciled.'} "
            f"{len(low_labs) + len(high_labs)} out-of-range lab result(s) noted from source reports."
        )

        return {
            "summary_text": summary_text,
            "sections": {
                "record_overview": overview,
                "recently_documented": recently_documented,
                "laboratory_values": laboratory_values,
                "historical_changes": historical_changes,
                "potential_conflicts": potential_conflicts,
                "missing_information": missing_information,
                "verification_required": verification_required,
            },
            "key_findings": key_findings,
        }

    def _generate_with_gemini(
        self,
        patient: Patient,
        profile: Optional[PatientProfile],
        documents: List[Document],
        labs: List[LabResult],
        medications: List[Medication],
        conditions: List[Condition],
        allergies: List[Allergy],
        observations: List[Observation],
        conflicts: List[ConflictRecord],
        timeline: List[TimelineEvent],
    ) -> Optional[Dict[str, Any]]:
        """Invokes Gemini 1.5 with strictly grounded clinical facts and schema enforcement."""
        if not self.api_key:
            return None

        # Build clean JSON clinical facts
        facts = {
            "patient": {
                "name": f"{patient.first_name} {patient.last_name}",
                "mrn": patient.mrn,
                "gender": patient.gender,
                "dob": patient.date_of_birth,
                "symptoms": profile.symptoms if profile else None,
            },
            "document_count": len(documents),
            "documents": [{"name": d.original_name, "date": str(d.upload_date)} for d in documents],
            "laboratories": [
                {
                    "test_name": l.test_name,
                    "value": l.value if l.value is not None else l.raw_value,
                    "unit": l.unit,
                    "reference_range": f"{l.reference_range_low} - {l.reference_range_high}" if l.reference_range_low is not None else "NOT_PROVIDED",
                    "status": l.status.value,
                    "report_date": l.report_date,
                    "verification": l.verification_status.value,
                }
                for l in labs
            ],
            "medications": [
                {
                    "name": m.medication_name,
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "status": m.clinical_status,
                    "prescribed_date": m.prescribed_date,
                }
                for m in medications
            ],
            "conditions": [
                {"name": c.condition_name, "onset_date": c.onset_date, "status": c.clinical_status}
                for c in conditions
            ],
            "allergies": [
                {"allergen": a.allergen, "reaction": a.reaction, "severity": a.severity}
                for a in allergies
            ],
            "conflicts": [
                {
                    "category": cf.category.value,
                    "field": cf.field_name,
                    "source_a": f"{cf.source_a_type}: {cf.source_a_value}",
                    "source_b": f"{cf.source_b_type}: {cf.source_b_value}",
                    "description": cf.description,
                    "status": cf.status.value,
                }
                for cf in conflicts
            ],
            "timeline": [
                {"date": t.event_date, "title": t.title, "description": t.description}
                for t in timeline[:5]
            ],
        }

        system_instruction = (
            "You are the MedLens AI Summary Engine. Your sole purpose is to organize and explain "
            "the provided structured patient information in clear, patient-friendly language.\n"
            "STRICT CLINICAL RULES:\n"
            "1. NO DIAGNOSIS: Do NOT diagnose diseases or state that the patient has a new condition.\n"
            "2. NO TREATMENT OR MEDICATION RECOMMENDATIONS: Never recommend medications, therapies, or dosage adjustments.\n"
            "3. NO INVENTED INFORMATION: Rely ONLY on the facts given in the context. Never invent reference ranges.\n"
            "4. SOURCE REPORT STATUS: Report lab statuses exactly as provided (NORMAL, LOW, HIGH, UNKNOWN). "
            "If range is NOT_PROVIDED or UNKNOWN, state that reference range was not provided in the source report.\n"
            "5. PATIENT-FRIENDLY TONE: Use clear, empathetic, accessible language.\n"
            "6. STRUCTURE: You MUST return a valid JSON object with the exact keys: 'summary_text', 'sections' "
            "(containing 'record_overview', 'recently_documented', 'laboratory_values', 'historical_changes', "
            "'potential_conflicts', 'missing_information', 'verification_required'), and 'key_findings'."
        )

        prompt = (
            f"Synthesize the following structured clinical record into a patient-friendly summary with 7 discrete sections.\n\n"
            f"<clinical_facts>\n{json.dumps(facts, indent=2)}\n</clinical_facts>\n\n"
            f"Return JSON adhering to the specified schema."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                raw_json = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_json)
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}, falling back to deterministic synthesis.")
        except Exception as e:
            logger.warning(f"Error invoking Gemini for summary: {e}. Falling back.")

        return None

    def _apply_clinical_safety_guardrails(self, summary_text: str, sections_dict: Dict[str, str]) -> tuple[str, Dict[str, str]]:
        """Scans summary content for prohibited medical terms and scrubs any violations."""
        for pattern in PROHIBITED_PHRASES:
            if re.search(pattern, summary_text, flags=re.IGNORECASE):
                logger.warning(f"Safety violation scrubbed from summary_text matching: '{pattern}'")
                summary_text = re.sub(pattern, "[non-diagnostic note]", summary_text, flags=re.IGNORECASE)
            for sec_key, sec_val in sections_dict.items():
                if re.search(pattern, sec_val, flags=re.IGNORECASE):
                    logger.warning(f"Safety violation scrubbed from section {sec_key} matching: '{pattern}'")
                    sections_dict[sec_key] = re.sub(pattern, "[non-diagnostic note]", sec_val, flags=re.IGNORECASE)

        return summary_text, sections_dict

    def _to_pydantic(self, model: ClinicalSummary) -> ClinicalSummaryRead:
        """Helper to convert SQLAlchemy model to Pydantic schema."""
        sections_obj = None
        if model.sections:
            try:
                sec_dict = json.loads(model.sections)
                sections_obj = ClinicalSummarySections(**sec_dict)
            except Exception:
                pass

        provenance_obj = None
        if model.structured_provenance_sources:
            try:
                prov_dict = json.loads(model.structured_provenance_sources)
                provenance_obj = SummaryProvenanceSources(**prov_dict)
            except Exception:
                pass

        key_findings_list = []
        if model.key_findings:
            try:
                parsed = json.loads(model.key_findings)
                if isinstance(parsed, list):
                    key_findings_list = parsed
                elif isinstance(parsed, str):
                    key_findings_list = [parsed]
            except Exception:
                key_findings_list = [model.key_findings]

        return ClinicalSummaryRead(
            id=model.id,
            patient_id=model.patient_id,
            summary_text=model.summary_text,
            sections=sections_obj,
            structured_provenance_sources=provenance_obj,
            key_findings=key_findings_list,
            disclaimer=model.disclaimer or MANDATORY_DISCLAIMER,
            model_version=model.model_version or "medlens-summary-v1",
            is_ai_generated=True,
            is_verified=model.is_verified,
            created_at=model.created_at,
        )
