import re
from typing import List, Tuple, Optional
from app.schemas.ai_extraction import (
    ExtractedDocumentData,
    ExtractedLabItem,
    ExtractedPatientInfo,
    ExtractedMedicationItem,
    ExtractedConditionItem,
    ExtractedAllergyItem,
)
from app.schemas.clinical import LabStatus
from app.services.reference_range_validator import ReferenceRangeValidator

CONFIDENCE_HUMAN_REVIEW_THRESHOLD = 0.85

class ClinicalValidationGate:
    """
    Deterministic Clinical Validation Gate
    
    The AI response must NEVER be directly trusted.
    Validates the AI extraction against the underlying source page text before database storage.
    
    Enforces:
    1. Grounding check: Verifies test names, medications, and conditions appear in page text.
    2. Anti-hallucination of reference ranges: If the AI populated reference bounds that do
       not appear anywhere in the source snippet or page text, nullifies them to prevent false ranges.
    3. Numerical precision consistency: Verifies parsed float matches raw_value string.
    4. Exact unit retention.
    5. Calibrated confidence and human verification flagging: Items with confidence < 0.85
       are flagged with requires_human_verification=True.
    6. Non-diagnostic status evaluation: Evaluates NORMAL/LOW/HIGH/UNKNOWN strictly using
       validated report bounds without clinical speculation.
    """

    @staticmethod
    def _normalize_text_for_search(text: str) -> str:
        """Lowers case and normalizes whitespace for loose substring verification."""
        return re.sub(r"\s+", " ", text.lower().strip())

    @classmethod
    def validate_lab_item(cls, lab: ExtractedLabItem, page_text: str) -> Tuple[ExtractedLabItem, List[str]]:
        """
        Validates a single extracted laboratory item against page text.
        Returns: (validated_lab_item, list_of_validation_notes)
        """
        notes = []
        norm_page = cls._normalize_text_for_search(page_text)
        norm_test = cls._normalize_text_for_search(lab.test_name)

        # 1. Grounding Check: Test name must appear in page text
        # If test name is not directly found, check if key words match
        test_words = [w for w in norm_test.split() if len(w) > 2]
        is_grounded = any(word in norm_page for word in test_words) if test_words else (norm_test in norm_page)
        
        if not is_grounded:
            notes.append(f"Grounding warning: Test '{lab.test_name}' not strongly matched in page text.")
            lab.confidence = min(lab.confidence, 0.60)
            lab.requires_human_verification = True

        # 2. Value Grounding & Precision Check
        if lab.raw_value:
            norm_raw = lab.raw_value.strip()
            # Ensure raw value appears in page
            if norm_raw.lower() not in norm_page:
                notes.append(f"Value '{lab.raw_value}' not found verbatim in page text.")
                lab.confidence = min(lab.confidence, 0.70)
                lab.requires_human_verification = True

            # If numeric value is parsed, verify consistency with raw_value
            if lab.value is not None:
                try:
                    # Check that numeric value digits match raw string
                    val_str = str(lab.value)
                    # Handle floats like 14.0 vs 14
                    clean_raw = re.sub(r"[^\d.]", "", norm_raw)
                    if clean_raw and abs(float(clean_raw) - lab.value) > 1e-4:
                        notes.append(f"Numerical mismatch: raw '{lab.raw_value}' vs parsed '{lab.value}'.")
                        lab.requires_human_verification = True
                except ValueError:
                    pass

        # 3. Reference Range Anti-Hallucination Protocol
        # MedLens Rule: Never invent reference ranges. If not printed, must be NULL.
        has_range = (
            lab.reference_range_low is not None or 
            lab.reference_range_high is not None or 
            lab.reference_range_text is not None
        )

        if has_range:
            range_grounded = False
            # Check if text snippet or page contains the range numbers
            low_str = str(lab.reference_range_low) if lab.reference_range_low is not None else ""
            high_str = str(lab.reference_range_high) if lab.reference_range_high is not None else ""
            txt_str = lab.reference_range_text.lower() if lab.reference_range_text else ""

            # If snippet is provided, check snippet first
            search_corpus = (lab.source_snippet or "").lower() + " " + norm_page

            if txt_str and txt_str in search_corpus:
                range_grounded = True
            elif low_str and high_str and (low_str in search_corpus or high_str in search_corpus):
                range_grounded = True
            elif any(s in search_corpus for s in [low_str, high_str] if s):
                range_grounded = True

            if not range_grounded:
                # The AI hallucinated/injected a standard range not present in the document!
                notes.append(
                    f"Hallucinated reference range detected for '{lab.test_name}'. "
                    f"Range ({lab.reference_range_low}-{lab.reference_range_high}) absent from document. "
                    "Enforcing NULL range."
                )
                lab.reference_range_low = None
                lab.reference_range_high = None
                lab.reference_range_text = None
                lab.requires_human_verification = True

        # 4. Confidence Thresholding
        if lab.confidence < CONFIDENCE_HUMAN_REVIEW_THRESHOLD:
            lab.requires_human_verification = True

        return lab, notes

    @classmethod
    def evaluate_lab_status(
        cls, 
        value: Optional[float], 
        low: Optional[float], 
        high: Optional[float],
        range_text: Optional[str] = None,
        unit: Optional[str] = None
    ) -> LabStatus:
        """
        Determines LabStatus strictly from report-derived bounds.
        Never infers status if bounds or value are absent.
        """
        res = ReferenceRangeValidator.validate(
            value=value,
            unit=unit,
            reference_range_low=low,
            reference_range_high=high,
            reference_range_text=range_text,
        )
        return res.status

    @classmethod
    def validate_extracted_data(
        cls, 
        data: ExtractedDocumentData, 
        pages_text_map: dict[int, str]
    ) -> ExtractedDocumentData:
        """
        Validates entire document extraction output against all source pages.
        Nullifies ungrounded fields, calculates confidence, sets human review flags.
        """
        all_notes = []
        has_unverified = False

        # 1. Validate Labs
        validated_labs: List[ExtractedLabItem] = []
        for lab in data.laboratories:
            page_text = pages_text_map.get(lab.source_page, "")
            validated_lab, notes = cls.validate_lab_item(lab, page_text)
            if notes:
                all_notes.extend(notes)
            if validated_lab.requires_human_verification:
                has_unverified = True
            validated_labs.append(validated_lab)

        data.laboratories = validated_labs

        # 2. Validate Patient Info
        # Check medications
        for med in data.patient_info.medications:
            page_text = pages_text_map.get(med.source_page, "")
            if cls._normalize_text_for_search(med.medication_name) not in cls._normalize_text_for_search(page_text):
                med.confidence = min(med.confidence, 0.70)
                med.requires_human_verification = True
                has_unverified = True

        # Check conditions
        for cond in data.patient_info.conditions:
            page_text = pages_text_map.get(cond.source_page, "")
            if cls._normalize_text_for_search(cond.condition_name) not in cls._normalize_text_for_search(page_text):
                cond.confidence = min(cond.confidence, 0.70)
                cond.requires_human_verification = True
                has_unverified = True

        # Check allergies
        for alg in data.patient_info.allergies:
            page_text = pages_text_map.get(alg.source_page, "")
            if cls._normalize_text_for_search(alg.allergen) not in cls._normalize_text_for_search(page_text):
                alg.confidence = min(alg.confidence, 0.70)
                alg.requires_human_verification = True
                has_unverified = True

        # Recalculate overall confidence
        confidences = [lab.confidence for lab in data.laboratories]
        confidences.extend([m.confidence for m in data.patient_info.medications])
        confidences.extend([c.confidence for c in data.patient_info.conditions])
        confidences.extend([a.confidence for a in data.patient_info.allergies])

        if confidences:
            data.overall_confidence = round(sum(confidences) / len(confidences), 3)
        else:
            data.overall_confidence = 1.0

        data.has_unverified_items = has_unverified or (data.overall_confidence < CONFIDENCE_HUMAN_REVIEW_THRESHOLD)

        if all_notes:
            existing_notes = data.extraction_notes or ""
            data.extraction_notes = (existing_notes + "\nValidation Notes: " + "; ".join(all_notes)).strip()

        return data
