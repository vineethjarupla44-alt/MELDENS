import os
import re
import json
import time
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import requests

from app.core.config import settings
from app.db.models import (
    Document,
    DocumentPage,
    Patient,
    LabResult,
    Medication,
    Condition,
    Allergy,
    AuditLog,
    ProvenanceSourceEnum,
    VerificationStatusEnum,
    LabStatusEnum,
)
from app.schemas.ai_extraction import (
    ExtractedDocumentData,
    ExtractedLabItem,
    ExtractedPatientInfo,
    ExtractedMedicationItem,
    ExtractedConditionItem,
    ExtractedAllergyItem,
)
from app.services.ai_prompts import SYSTEM_EXTRACTION_PROMPT, build_page_extraction_prompt
from app.services.clinical_validator import ClinicalValidationGate
from app.services.reference_range_validator import ReferenceRangeValidator


# ---------------------------------------------------------------------------
# Privacy-Preserving Logger (Redacts PHI from system logs)
# ---------------------------------------------------------------------------
logger = logging.getLogger("medlens.ai_extraction")

def sanitize_log_message(msg: str) -> str:
    """Redacts potential patient names, MRNs, and sensitive numbers from logs."""
    # Redact MRN patterns
    msg = re.sub(r"MED-[A-Z0-9-]+", "[REDACTED_MRN]", msg)
    # Redact common date formats
    msg = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "[REDACTED_DATE]", msg)
    # Redact names if explicitly prefixed
    msg = re.sub(r"(Patient Name:\s*)([A-Za-z\s]+)", r"\1[REDACTED_NAME]", msg)
    return msg

class PrivacyPreservingLogFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        return True

logger.addFilter(PrivacyPreservingLogFilter())

# ---------------------------------------------------------------------------
# AI Extraction Service
# ---------------------------------------------------------------------------
class AIExtractionService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.LLM_MODEL or "gemini-1.5-pro"
        self.validator = ClinicalValidationGate()

    def _call_gemini_api_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[dict]:
        """
        Invokes Google Gemini REST API using structured JSON output.
        Handles rate limits and transient network errors with exponential backoff.
        """
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_EXTRACTION_PROMPT}]
            },
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            }
        }

        backoff = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Dispatching extraction request to Gemini (Attempt {attempt}/{max_retries}).")
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(raw_content)
                elif resp.status_code in (429, 500, 503):
                    logger.warning(f"Transient HTTP {resp.status_code} from Gemini. Backing off for {backoff:.1f}s.")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error(f"Gemini API returned unrecoverable status {resp.status_code}: {resp.text[:120]}")
                    break
            except Exception as e:
                logger.warning(f"Error calling Gemini on attempt {attempt}: {str(e)}")
                time.sleep(backoff)
                backoff *= 2

        return None

    def _rule_based_fallback_extract(self, page_number: int, page_text: str) -> dict:
        """
        Deterministic, high-fidelity rule-based extraction engine.
        Acts as the offline fallback when API key is unavailable or quota is exceeded.
        Strictly adheres to:
        - Extract only explicit data
        - Never invent reference ranges (NULL if not printed)
        - Preserves numerical precision and verbatim units
        - Assigns confidence scores
        """
        lines = page_text.splitlines()
        patient_info = {
            "age": None,
            "sex": None,
            "symptoms": [],
            "conditions": [],
            "allergies": [],
            "medications": [],
        }
        laboratories = []

        # 1. Demographic extraction
        for line in lines:
            line_str = line.strip()
            # Age
            age_match = re.search(r"\b(?:Age|AGE)[:\s]+(\d{1,3})\b", line_str)
            if age_match and patient_info["age"] is None:
                patient_info["age"] = int(age_match.group(1))

            # Sex
            sex_match = re.search(r"\b(?:Sex|Gender)[:\s]+(Male|Female|M|F)\b", line_str, re.IGNORECASE)
            if sex_match and patient_info["sex"] is None:
                s = sex_match.group(1).upper()
                patient_info["sex"] = "MALE" if s.startswith("M") else "FEMALE"

            # Symptoms
            sym_match = re.search(r"(?:Symptoms?|Chief Complaint)[:\s]+([^.]+)", line_str, re.IGNORECASE)
            if sym_match:
                symptoms_raw = sym_match.group(1).split(",")
                for sym in symptoms_raw:
                    s_clean = sym.strip()
                    if s_clean and len(s_clean) > 2:
                        patient_info["symptoms"].append(s_clean)

            # Allergies
            alg_match = re.search(r"Allerg(?:ies|y)[:\s]+([^.]+)", line_str, re.IGNORECASE)
            if alg_match:
                for alg in alg_match.group(1).split(","):
                    a_clean = alg.strip()
                    if a_clean and a_clean.lower() != "none" and a_clean.lower() != "nkda":
                        # Check if reaction mentioned e.g. Penicillin (Rash)
                        react_m = re.search(r"([A-Za-z\s]+)(?:\(([^)]+)\))?", a_clean)
                        if react_m:
                            patient_info["allergies"].append({
                                "allergen": react_m.group(1).strip(),
                                "reaction": react_m.group(2).strip() if react_m.group(2) else None,
                                "severity": None,
                                "source_page": page_number,
                                "confidence": 0.95,
                                "source_snippet": line_str[:60],
                                "requires_human_verification": False,
                            })

            # Medications
            med_match = re.search(r"(?:Prescribed|Medications?|Rx)[:\s]+([^.]+)", line_str, re.IGNORECASE)
            if med_match:
                for med in med_match.group(1).split(","):
                    m_clean = med.strip()
                    if m_clean and len(m_clean) > 2:
                        patient_info["medications"].append({
                            "medication_name": m_clean,
                            "dosage": None,
                            "frequency": None,
                            "route": None,
                            "source_page": page_number,
                            "confidence": 0.90,
                            "source_snippet": line_str[:60],
                            "requires_human_verification": False,
                        })

            # Conditions
            cond_match = re.search(r"(?:Assessment|Impression|Diagnosis|History)[:\s]+([^.]+)", line_str, re.IGNORECASE)
            if cond_match:
                c_clean = cond_match.group(1).strip()
                if c_clean and len(c_clean) > 3:
                    patient_info["conditions"].append({
                        "condition_name": c_clean,
                        "onset_date": None,
                        "source_page": page_number,
                        "confidence": 0.90,
                        "source_snippet": line_str[:60],
                        "requires_human_verification": False,
                    })

        # 2. Laboratory extraction (Table / line matching)
        skip_prefixes = (
            "patient", "mrn", "chief complaint", "symptom", "known allergies",
            "allerg", "current medications", "medication", "prescrib", "system override",
            "assessment", "impression", "doctor", "history", "vital", "bp", "page",
        )

        lab_line_pattern = re.compile(
            r"^([A-Za-z0-9\s\(\)/-]+?)[:\s]{1,4}"
            r"(~?\d+(?:\.\d+)?)\s*"
            r"([a-zA-Z/%^0-9]+)?"
            r"(?:\s*(?:\(|\[)?(?:Ref|Reference|Interval)?[:\s]*(\d+(?:\.\d+)?)\s*[-–—to]+\s*(\d+(?:\.\d+)?)(?:\)|\])?)?"
            r"(?:\s+(NORMAL|HIGH|LOW|CRITICAL|ABNORMAL))?",
            re.IGNORECASE
        )

        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) < 5:
                continue

            # Skip obvious header lines
            if "Test Name" in line_str or "Units" in line_str or "Result" in line_str or "LABORATORY FINDINGS" in line_str:
                continue

            # Skip non-lab clinical sections
            lower_line = line_str.lower()
            if any(lower_line.startswith(prefix) for prefix in skip_prefixes):
                continue

            match = lab_line_pattern.search(line_str)
            if match:
                test_name = match.group(1).strip()
                val_raw = match.group(2).strip()
                unit = match.group(3).strip() if match.group(3) else None
                ref_low = match.group(4)
                ref_high = match.group(5)
                obs_flag = match.group(6)

                # Filter out ordinary prose
                if len(test_name) < 3 or test_name.lower() in ("page", "patient", "age", "mrn", "doctor", "bp", "date"):
                    continue

                # Parse float value
                clean_num_str = re.sub(r"[^\d.]", "", val_raw)
                val_float = float(clean_num_str) if clean_num_str else None
                low_float = float(ref_low) if ref_low else None
                high_float = float(ref_high) if ref_high else None
                ref_text = f"{ref_low} - {ref_high}" if (ref_low and ref_high) else None

                confidence = 0.95
                requires_human = False
                if "~" in val_raw or "borderline" in line_str.lower() or "approximate" in line_str.lower():
                    confidence = 0.75
                    requires_human = True

                # Rule 6 & 7: If reference range is absent from the report, return strictly NULL
                laboratories.append({
                    "test_name": test_name,
                    "raw_value": val_raw,
                    "value": val_float,
                    "unit": unit,
                    "reference_range_low": low_float,
                    "reference_range_high": high_float,
                    "reference_range_text": ref_text,
                    "observation": obs_flag if obs_flag else None,
                    "report_date": None,
                    "source_page": page_number,
                    "confidence": confidence,
                    "source_snippet": line_str[:80],
                    "requires_human_verification": requires_human,
                })


        return {
            "patient_info": patient_info,
            "laboratories": laboratories,
            "extraction_notes": "Processed via deterministic clinical rule-based engine.",
            "overall_confidence": 0.95,
        }

    def extract_and_validate_page(self, page_number: int, page_text: str) -> dict:
        """Extracts medical data from a single page using Gemini or fallback engine."""
        prompt = build_page_extraction_prompt(page_number, page_text)
        
        extracted_raw = None
        if self.api_key:
            extracted_raw = self._call_gemini_api_with_retry(prompt)

        if not extracted_raw:
            logger.info(f"Using deterministic clinical fallback engine for Page {page_number}.")
            extracted_raw = self._rule_based_fallback_extract(page_number, page_text)

        return extracted_raw

    def extract_document_medical_data(self, document_id: str) -> ExtractedDocumentData:
        """
        Full Document AI Extraction Pipeline:
        1. Retrieves document and all page texts.
        2. Dispatches extraction page-by-page.
        3. Aggregates results into ExtractedDocumentData schema.
        4. Passes entire dataset through ClinicalValidationGate.
        5. Persists validated items into database (LabResult, Medication, Condition, Allergy).
        6. Logs sanitized audit metrics.
        7. Returns validated Pydantic model.
        """
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        pages = (
            self.db.query(DocumentPage)
            .filter(DocumentPage.document_id == document_id)
            .order_by(DocumentPage.page_number.asc())
            .all()
        )

        if not pages:
            raise HTTPException(status_code=400, detail="Document has not undergone text extraction yet. Run /process first.")

        pages_text_map = {p.page_number: (p.extracted_text or "") for p in pages}
        pages_id_map = {p.page_number: p.id for p in pages}

        aggregated_patient_info = ExtractedPatientInfo()
        aggregated_labs: List[ExtractedLabItem] = []
        processed_pages: List[int] = []

        # 1. Page-by-page AI extraction
        for p in pages:
            if not p.extracted_text or p.extraction_status == "OCR_REQUIRED":
                continue

            processed_pages.append(p.page_number)
            raw_page_data = self.extract_and_validate_page(p.page_number, p.extracted_text)

            # Aggregate patient info
            p_info = raw_page_data.get("patient_info", {})
            if p_info.get("age") is not None and aggregated_patient_info.age is None:
                aggregated_patient_info.age = p_info["age"]
            if p_info.get("sex") is not None and aggregated_patient_info.sex is None:
                aggregated_patient_info.sex = p_info["sex"]
            
            for sym in p_info.get("symptoms", []):
                if sym not in aggregated_patient_info.symptoms:
                    aggregated_patient_info.symptoms.append(sym)

            for med in p_info.get("medications", []):
                aggregated_patient_info.medications.append(ExtractedMedicationItem(**med))

            for cond in p_info.get("conditions", []):
                aggregated_patient_info.conditions.append(ExtractedConditionItem(**cond))

            for alg in p_info.get("allergies", []):
                aggregated_patient_info.allergies.append(ExtractedAllergyItem(**alg))

            # Aggregate laboratories
            for lab in raw_page_data.get("laboratories", []):
                aggregated_labs.append(ExtractedLabItem(**lab))

        unvalidated_data = ExtractedDocumentData(
            document_id=doc.id,
            patient_info=aggregated_patient_info,
            laboratories=aggregated_labs,
            overall_confidence=0.95,
            processed_pages=processed_pages,
        )

        # 2. Deterministic Clinical Validation Gate (Never Trust AI Directly)
        validated_data = self.validator.validate_extracted_data(unvalidated_data, pages_text_map)

        # 3. Database Persistence
        # A. Store Lab Results
        for lab in validated_data.laboratories:
            page_id = pages_id_map.get(lab.source_page)

            # Deterministic Reference Range Validator
            # Validates report bounds, parses numeric values safely, preserves original range text verbatim
            range_val = ReferenceRangeValidator.validate(
                value=lab.value if lab.value is not None else lab.raw_value,
                unit=lab.unit,
                reference_range_low=lab.reference_range_low,
                reference_range_high=lab.reference_range_high,
                reference_range_text=lab.reference_range_text,
                raw_value=lab.raw_value,
            )

            # Flag for human verification if invalid bounds or parse ambiguity
            if not range_val.is_valid:
                lab.requires_human_verification = True

            db_lab = LabResult(
                patient_id=doc.patient_id,
                document_id=doc.id,
                page_id=page_id,
                test_name=lab.test_name,
                raw_value=lab.raw_value,
                value=range_val.value,
                unit=lab.unit,
                reference_range_low=range_val.reference_range_low,
                reference_range_high=range_val.reference_range_high,
                reference_range_text=lab.reference_range_text,  # Preserve verbatim from report
                status=LabStatusEnum(range_val.status.value),
                report_date=lab.report_date,
                provenance_source=ProvenanceSourceEnum.AI_GENERATED,
                source_document=doc.original_name,
                source_page=lab.source_page,
                confidence=lab.confidence,
                source_snippet=lab.source_snippet,
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_lab)

        # B. Store Medications
        for med in validated_data.patient_info.medications:
            page_id = pages_id_map.get(med.source_page)
            db_med = Medication(
                patient_id=doc.patient_id,
                document_id=doc.id,
                page_id=page_id,
                medication_name=med.medication_name,
                dosage=med.dosage,
                frequency=med.frequency,
                route=med.route,
                raw_text=med.source_snippet,
                provenance_source=ProvenanceSourceEnum.AI_GENERATED,
                source_document=doc.original_name,
                source_page=med.source_page,
                confidence=med.confidence,
                source_snippet=med.source_snippet,
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_med)

        # C. Store Conditions
        for cond in validated_data.patient_info.conditions:
            page_id = pages_id_map.get(cond.source_page)
            db_cond = Condition(
                patient_id=doc.patient_id,
                document_id=doc.id,
                page_id=page_id,
                condition_name=cond.condition_name,
                raw_text=cond.source_snippet,
                provenance_source=ProvenanceSourceEnum.AI_GENERATED,
                source_document=doc.original_name,
                source_page=cond.source_page,
                confidence=cond.confidence,
                source_snippet=cond.source_snippet,
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_cond)

        # D. Store Allergies
        for alg in validated_data.patient_info.allergies:
            page_id = pages_id_map.get(alg.source_page)
            db_alg = Allergy(
                patient_id=doc.patient_id,
                document_id=doc.id,
                page_id=page_id,
                allergen=alg.allergen,
                reaction=alg.reaction,
                severity=alg.severity,
                raw_text=alg.source_snippet,
                provenance_source=ProvenanceSourceEnum.AI_GENERATED,
                source_document=doc.original_name,
                source_page=alg.source_page,
                confidence=alg.confidence,
                source_snippet=alg.source_snippet,
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_alg)

        # 4. Sanitized Audit Log (Zero PHI in log content)
        audit_state = json.dumps({
            "labs_extracted": len(validated_data.laboratories),
            "medications_extracted": len(validated_data.patient_info.medications),
            "conditions_extracted": len(validated_data.patient_info.conditions),
            "allergies_extracted": len(validated_data.patient_info.allergies),
            "overall_confidence": validated_data.overall_confidence,
            "has_unverified_items": validated_data.has_unverified_items,
        })
        audit = AuditLog(
            entity_type="Document",
            entity_id=doc.id,
            action="AI_EXTRACTION",
            actor_id="AI_EXTRACTION_ENGINE",
            actor_name="AIExtractionService",
            new_state=audit_state,
            change_reason=f"Extracted {len(validated_data.laboratories)} labs with confidence {validated_data.overall_confidence:.2f}.",
        )
        self.db.add(audit)
        self.db.commit()

        logger.info(f"AI extraction completed for Document {doc.id[:8]}. Extracted {len(validated_data.laboratories)} labs.")
        return validated_data
