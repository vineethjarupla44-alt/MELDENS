import re
from typing import Optional, Tuple, List, Union
from pydantic import BaseModel, Field
from app.schemas.clinical import LabStatus

class RangeValidationResult(BaseModel):
    status: LabStatus
    value: Optional[float] = None
    raw_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    reference_range_text: Optional[str] = None
    is_valid: bool = True
    validation_notes: List[str] = Field(default_factory=list)

class ReferenceRangeValidator:
    """
    Deterministic Laboratory Reference-Range Validation Service
    
    Guarantees:
    1. Reference ranges must originate from the source report.
    2. Never creates a default or inferred reference range.
    3. Never uses external medical knowledge or standard population tables.
    4. Deterministic computation: Never asks LLM to calculate clinical status.
    5. Safe numeric parsing handling commas, inequality signs, and whitespace.
    6. Safe handling of invalid, missing, or non-numeric values.
    7. Parses text-represented reference ranges (e.g. "12-16", "12–16", "<200", ">60").
    8. Preserves original reference_range_text verbatim.
    
    Core Rules:
    - IF reference range is missing: status = UNKNOWN
    - IF value < reference_range_low: status = LOW
    - IF value > reference_range_high: status = HIGH
    - OTHERWISE: status = NORMAL
    """

    @classmethod
    def safe_parse_float(cls, val: Union[float, int, str, None]) -> Optional[float]:
        """Safely parses numbers from various formats including European comma decimals."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        
        val_str = str(val).strip()
        if not val_str:
            return None

        # Replace European comma decimal if no period exists
        if "," in val_str and "." not in val_str:
            val_str = val_str.replace(",", ".")

        # Strip inequality prefixes like <, >, <=, >=, ~
        clean_str = re.sub(r"^[<>=~≤≥\s]+", "", val_str)

        # Match decimal or scientific notation number
        match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", clean_str)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
        return None

    @classmethod
    def parse_text_range(cls, text: Optional[str]) -> Tuple[Optional[float], Optional[float], List[str]]:
        """
        Parses text representation of reference ranges:
        - "12 - 16", "12–16" (en-dash), "12 to 16" -> (12.0, 16.0)
        - "< 200", "<= 200", "up to 200" -> (None, 200.0)
        - "> 60", ">= 60" -> (60.0, None)
        - Malformed text ("N/A", "See Note", "abc - def") -> (None, None)
        """
        notes = []
        if not text:
            return None, None, notes

        clean_text = text.strip()
        if not clean_text:
            return None, None, notes

        # 1. Dual bound pattern: "12 - 16", "12–16", "12.5 to 16.0"
        dual_match = re.search(
            r"([-+]?\d*[.,]?\d+)\s*(?:[-–—to:]+|\s+to\s+)\s*([-+]?\d*[.,]?\d+)",
            clean_text,
            re.IGNORECASE
        )
        if dual_match:
            low = cls.safe_parse_float(dual_match.group(1))
            high = cls.safe_parse_float(dual_match.group(2))
            if low is not None and high is not None:
                if low > high:
                    notes.append(f"Inverted range detected: low ({low}) > high ({high}). Cannot validate safely.")
                return low, high, notes

        # 2. Upper bound only: "< 200", "<= 200", "up to 200", "<200"
        upper_match = re.search(r"(?:<|<=|≤|up to|less than)\s*([-+]?\d*[.,]?\d+)", clean_text, re.IGNORECASE)
        if upper_match:
            high = cls.safe_parse_float(upper_match.group(1))
            return None, high, notes

        # 3. Lower bound only: "> 60", ">= 60", "greater than 60"
        lower_match = re.search(r"(?:>|>=|≥|greater than)\s*([-+]?\d*[.,]?\d+)", clean_text, re.IGNORECASE)
        if lower_match:
            low = cls.safe_parse_float(lower_match.group(1))
            return low, None, notes

        # Non-parseable or qualitative range
        notes.append(f"Could not parse numeric bounds from range text: '{clean_text}'.")
        return None, None, notes

    @classmethod
    def validate(
        cls,
        value: Union[float, int, str, None],
        unit: Optional[str] = None,
        reference_range_low: Union[float, int, str, None] = None,
        reference_range_high: Union[float, int, str, None] = None,
        reference_range_text: Optional[str] = None,
        raw_value: Optional[str] = None,
    ) -> RangeValidationResult:
        """
        Determines the clinical status strictly using deterministic range evaluation.
        
        Rules:
        IF reference range is missing: status = UNKNOWN
        IF value < reference_range_low: status = LOW
        IF value > reference_range_high: status = HIGH
        OTHERWISE: status = NORMAL
        """
        notes: List[str] = []

        # 1. Parse value safely
        parsed_val = cls.safe_parse_float(value)
        if parsed_val is None and value is not None:
            notes.append(f"Non-numeric value '{value}' cannot be evaluated against numeric reference ranges.")

        # 2. Resolve low and high bounds
        low = cls.safe_parse_float(reference_range_low)
        high = cls.safe_parse_float(reference_range_high)

        # 3. If explicit bounds missing but range text exists, attempt to parse from text
        if low is None and high is None and reference_range_text:
            parsed_text_low, parsed_text_high, text_notes = cls.parse_text_range(reference_range_text)
            low = parsed_text_low
            high = parsed_text_high
            notes.extend(text_notes)

        # 4. Check for inverted bounds
        if low is not None and high is not None and low > high:
            notes.append(f"Inverted bounds detected: low ({low}) > high ({high}). Marked UNKNOWN.")
            return RangeValidationResult(
                status=LabStatus.UNKNOWN,
                value=parsed_val,
                raw_value=str(value) if raw_value is None and value is not None else raw_value,
                unit=unit,
                reference_range_low=low,
                reference_range_high=high,
                reference_range_text=reference_range_text,
                is_valid=False,
                validation_notes=notes,
            )

        # 5. Core Evaluation Logic
        # IF value is missing or non-numeric: status = UNKNOWN
        if parsed_val is None:
            return RangeValidationResult(
                status=LabStatus.UNKNOWN,
                value=None,
                raw_value=str(value) if raw_value is None and value is not None else raw_value,
                unit=unit,
                reference_range_low=low,
                reference_range_high=high,
                reference_range_text=reference_range_text,
                is_valid=False,
                validation_notes=notes,
            )

        # IF reference range is missing: status = UNKNOWN
        # (Both low and high are None, meaning no range was given in the source report)
        if low is None and high is None:
            return RangeValidationResult(
                status=LabStatus.UNKNOWN,
                value=parsed_val,
                raw_value=str(value) if raw_value is None and value is not None else raw_value,
                unit=unit,
                reference_range_low=None,
                reference_range_high=None,
                reference_range_text=reference_range_text,
                is_valid=True,
                validation_notes=notes,
            )

        # Dual Bound Evaluation: low <= val <= high
        if low is not None and high is not None:
            if parsed_val < low:
                status = LabStatus.LOW
            elif parsed_val > high:
                status = LabStatus.HIGH
            else:
                status = LabStatus.NORMAL

        # Upper Bound Only Evaluation (e.g. Total Cholesterol < 200)
        elif low is None and high is not None:
            if parsed_val > high:
                status = LabStatus.HIGH
            else:
                status = LabStatus.NORMAL

        # Lower Bound Only Evaluation (e.g. eGFR > 60)
        elif low is not None and high is None:
            if parsed_val < low:
                status = LabStatus.LOW
            else:
                status = LabStatus.NORMAL

        else:
            status = LabStatus.UNKNOWN

        return RangeValidationResult(
            status=status,
            value=parsed_val,
            raw_value=str(value) if raw_value is None and value is not None else raw_value,
            unit=unit,
            reference_range_low=low,
            reference_range_high=high,
            reference_range_text=reference_range_text,
            is_valid=True,
            validation_notes=notes,
        )
