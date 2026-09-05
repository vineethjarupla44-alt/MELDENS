"""
Unit Tests for Deterministic Laboratory Reference-Range Validation Service

Tests all requirements:
- 10 vs 12–16 -> LOW
- 14 vs 12–16 -> NORMAL
- 18 vs 12–16 -> HIGH
- 14 vs missing range -> UNKNOWN
- Malformed / text-based ranges (en-dash, commas, inequalities, invalid strings)
- Preservation of original reference_range_text
"""
from app.services.reference_range_validator import ReferenceRangeValidator
from app.schemas.clinical import LabStatus

def run_tests():
    print("================================================================================")
    print("REFERENCE-RANGE VALIDATOR UNIT TESTS")
    print("================================================================================")

    # 1. 10 vs 12–16 -> LOW
    print("\n--- TEST 1: 10 vs 12–16 -> LOW ---")
    res1 = ReferenceRangeValidator.validate(
        value=10,
        unit="g/dL",
        reference_range_low=12,
        reference_range_high=16,
        reference_range_text="12–16"
    )
    print(f"  Result: status={res1.status}, val={res1.value}, range=[{res1.reference_range_low} - {res1.reference_range_high}]")
    assert res1.status == LabStatus.LOW
    assert res1.reference_range_text == "12–16"
    print("  [PASS] 10 vs 12–16 evaluated as LOW")

    # 2. 14 vs 12–16 -> NORMAL
    print("\n--- TEST 2: 14 vs 12–16 -> NORMAL ---")
    res2 = ReferenceRangeValidator.validate(
        value=14,
        unit="g/dL",
        reference_range_low=12,
        reference_range_high=16,
        reference_range_text="12–16"
    )
    print(f"  Result: status={res2.status}, val={res2.value}, range=[{res2.reference_range_low} - {res2.reference_range_high}]")
    assert res2.status == LabStatus.NORMAL
    print("  [PASS] 14 vs 12–16 evaluated as NORMAL")

    # 3. 18 vs 12–16 -> HIGH
    print("\n--- TEST 3: 18 vs 12–16 -> HIGH ---")
    res3 = ReferenceRangeValidator.validate(
        value=18,
        unit="g/dL",
        reference_range_low=12,
        reference_range_high=16,
        reference_range_text="12–16"
    )
    print(f"  Result: status={res3.status}, val={res3.value}, range=[{res3.reference_range_low} - {res3.reference_range_high}]")
    assert res3.status == LabStatus.HIGH
    print("  [PASS] 18 vs 12–16 evaluated as HIGH")

    # 4. 14 vs missing range -> UNKNOWN
    print("\n--- TEST 4: 14 vs missing range -> UNKNOWN ---")
    res4 = ReferenceRangeValidator.validate(
        value=14,
        unit="g/dL",
        reference_range_low=None,
        reference_range_high=None,
        reference_range_text=None
    )
    print(f"  Result: status={res4.status}, range=[{res4.reference_range_low} - {res4.reference_range_high}]")
    assert res4.status == LabStatus.UNKNOWN
    assert res4.reference_range_low is None
    assert res4.reference_range_high is None
    print("  [PASS] 14 vs missing range evaluated as UNKNOWN (Never invented)")

    # 5. Text-based ranges: "12–16" (En-dash) parsed when low/high not explicitly supplied
    print("\n--- TEST 5: Text-based range '12–16' with en-dash ---")
    res5_low = ReferenceRangeValidator.validate(value=10, reference_range_text="12–16")
    res5_norm = ReferenceRangeValidator.validate(value=14, reference_range_text="12–16")
    res5_high = ReferenceRangeValidator.validate(value=18, reference_range_text="12–16")
    assert res5_low.status == LabStatus.LOW
    assert res5_norm.status == LabStatus.NORMAL
    assert res5_high.status == LabStatus.HIGH
    print("  [PASS] En-dash text '12–16' successfully parsed and evaluated")

    # 6. Boundary values: exact lower bound and exact upper bound -> NORMAL
    print("\n--- TEST 6: Exact boundary values (12 and 16) ---")
    res_b_low = ReferenceRangeValidator.validate(value=12, reference_range_low=12, reference_range_high=16)
    res_b_high = ReferenceRangeValidator.validate(value=16, reference_range_low=12, reference_range_high=16)
    assert res_b_low.status == LabStatus.NORMAL
    assert res_b_high.status == LabStatus.NORMAL
    print("  [PASS] Exact boundaries are correctly evaluated as NORMAL")

    # 7. Upper-bound only: "< 200" (e.g. Total Cholesterol)
    print("\n--- TEST 7: Upper-bound only ('< 200') ---")
    res_chol_norm = ReferenceRangeValidator.validate(value=175, reference_range_text="< 200")
    res_chol_high = ReferenceRangeValidator.validate(value=225, reference_range_text="< 200")
    assert res_chol_norm.status == LabStatus.NORMAL
    assert res_chol_high.status == LabStatus.HIGH
    print("  [PASS] Upper-bound only (< 200) evaluated correctly")

    # 8. Lower-bound only: "> 60" (e.g. eGFR)
    print("\n--- TEST 8: Lower-bound only ('> 60') ---")
    res_egfr_norm = ReferenceRangeValidator.validate(value=85, reference_range_text="> 60")
    res_egfr_low = ReferenceRangeValidator.validate(value=45, reference_range_text="> 60")
    assert res_egfr_norm.status == LabStatus.NORMAL
    assert res_egfr_low.status == LabStatus.LOW
    print("  [PASS] Lower-bound only (> 60) evaluated correctly")

    # 9. European comma decimal numbers: "14,2" vs "12,0 - 16,0"
    print("\n--- TEST 9: European comma decimal formatting ---")
    res_comma = ReferenceRangeValidator.validate(value="14,2", reference_range_text="12,0 - 16,0")
    assert res_comma.status == LabStatus.NORMAL
    assert res_comma.value == 14.2
    assert res_comma.reference_range_low == 12.0
    assert res_comma.reference_range_high == 16.0
    print("  [PASS] Comma decimals parsed and evaluated cleanly")

    # 10. Malformed text ranges: "See Note", "N/A", "Variable", "abc - def"
    print("\n--- TEST 10: Malformed text ranges ---")
    res_malformed1 = ReferenceRangeValidator.validate(value=14, reference_range_text="See Note")
    res_malformed2 = ReferenceRangeValidator.validate(value=14, reference_range_text="N/A")
    res_malformed3 = ReferenceRangeValidator.validate(value=14, reference_range_text="abc - def")
    assert res_malformed1.status == LabStatus.UNKNOWN
    assert res_malformed2.status == LabStatus.UNKNOWN
    assert res_malformed3.status == LabStatus.UNKNOWN
    assert res_malformed1.reference_range_text == "See Note"
    print("  [PASS] Malformed text ranges safely evaluated as UNKNOWN while preserving text")

    # 11. Inverted range: "16 - 12"
    print("\n--- TEST 11: Inverted range ('16 - 12') ---")
    res_inverted = ReferenceRangeValidator.validate(value=14, reference_range_text="16 - 12")
    assert res_inverted.status == LabStatus.UNKNOWN
    assert res_inverted.is_valid is False
    print("  [PASS] Inverted range safely handled as UNKNOWN with validation warning")

    # 12. Non-numeric value: "Inconclusive", "Hemolyzed", None
    print("\n--- TEST 12: Non-numeric / missing value ---")
    res_non_num = ReferenceRangeValidator.validate(value="Inconclusive", reference_range_text="12–16")
    res_none = ReferenceRangeValidator.validate(value=None, reference_range_text="12–16")
    assert res_non_num.status == LabStatus.UNKNOWN
    assert res_none.status == LabStatus.UNKNOWN
    print("  [PASS] Non-numeric and None values evaluated as UNKNOWN")

    print("\n================================================================================")
    print("ALL REFERENCE-RANGE VALIDATOR TESTS PASSED (100% SUCCESS)!")
    print("================================================================================")

if __name__ == "__main__":
    run_tests()
