from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.db.models import (
    LabResult,
    Medication,
    Condition,
    Allergy,
    Observation,
    LabStatusEnum,
    ProvenanceSourceEnum,
    VerificationStatusEnum,
)
from app.schemas.clinical import (
    LabResultCreate,
    MedicationCreate,
    ConditionCreate,
    AllergyCreate,
    ObservationCreate,
    LabStatus,
)

def evaluate_lab_status(
    value: Optional[float],
    low: Optional[float],
    high: Optional[float]
) -> LabStatusEnum:
    """
    Strict clinical deterministic evaluation:
    - If value is None OR (low is None AND high is None), returns UNKNOWN.
    - NEVER auto-populates generic ranges.
    - Strictly obeys report-provided ranges only.
    """
    if value is None:
        return LabStatusEnum.UNKNOWN

    if low is None and high is None:
        return LabStatusEnum.UNKNOWN

    if low is not None and high is not None:
        if value < low:
            return LabStatusEnum.LOW
        elif value > high:
            return LabStatusEnum.HIGH
        else:
            return LabStatusEnum.NORMAL

    if low is not None and high is None:
        return LabStatusEnum.LOW if value < low else LabStatusEnum.NORMAL

    if high is not None and low is None:
        return LabStatusEnum.HIGH if value > high else LabStatusEnum.NORMAL

    return LabStatusEnum.UNKNOWN


class ClinicalRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Lab Results ---
    def add_lab_result(self, lab_in: LabResultCreate) -> LabResult:
        # Determine status strictly from document-provided bounds
        computed_status = evaluate_lab_status(
            lab_in.value,
            lab_in.reference_range_low,
            lab_in.reference_range_high
        )

        db_lab = LabResult(
            patient_id=lab_in.patient_id,
            document_id=lab_in.document_id,
            page_id=lab_in.page_id,
            test_name=lab_in.test_name,
            raw_value=lab_in.raw_value or (str(lab_in.value) if lab_in.value is not None else None),
            value=lab_in.value,
            unit=lab_in.unit,
            reference_range_low=lab_in.reference_range_low,
            reference_range_high=lab_in.reference_range_high,
            reference_range_text=lab_in.reference_range_text,
            status=computed_status,
            report_date=lab_in.report_date,
            provenance_source=ProvenanceSourceEnum(lab_in.provenance_source.value),
            source_document=lab_in.source_document,
            source_page=lab_in.source_page,
            confidence=lab_in.confidence,
            source_snippet=lab_in.source_snippet,
            verification_status=VerificationStatusEnum(lab_in.verification_status.value),
            verified_by=lab_in.verified_by,
            verified_at=lab_in.verified_at,
        )
        self.db.add(db_lab)
        self.db.commit()
        self.db.refresh(db_lab)
        return db_lab

    def list_labs_by_patient(self, patient_id: str) -> List[LabResult]:
        return (
            self.db.query(LabResult)
            .filter(LabResult.patient_id == patient_id)
            .order_by(LabResult.report_date.desc().nullslast())
            .all()
        )

    # --- Medications ---
    def add_medication(self, med_in: MedicationCreate) -> Medication:
        db_med = Medication(
            patient_id=med_in.patient_id,
            document_id=med_in.document_id,
            page_id=med_in.page_id,
            medication_name=med_in.medication_name,
            dosage=med_in.dosage,
            frequency=med_in.frequency,
            route=med_in.route,
            clinical_status=med_in.clinical_status,
            prescribed_date=med_in.prescribed_date,
            raw_text=med_in.raw_text,
            provenance_source=ProvenanceSourceEnum(med_in.provenance_source.value),
            source_document=med_in.source_document,
            source_page=med_in.source_page,
            confidence=med_in.confidence,
            source_snippet=med_in.source_snippet,
            verification_status=VerificationStatusEnum(med_in.verification_status.value),
            verified_by=med_in.verified_by,
            verified_at=med_in.verified_at,
        )
        self.db.add(db_med)
        self.db.commit()
        self.db.refresh(db_med)
        return db_med

    def list_meds_by_patient(self, patient_id: str) -> List[Medication]:
        return (
            self.db.query(Medication)
            .filter(Medication.patient_id == patient_id)
            .order_by(Medication.prescribed_date.desc().nullslast())
            .all()
        )

    # --- Conditions ---
    def add_condition(self, cond_in: ConditionCreate) -> Condition:
        db_cond = Condition(
            patient_id=cond_in.patient_id,
            document_id=cond_in.document_id,
            page_id=cond_in.page_id,
            condition_name=cond_in.condition_name,
            icd10_code=cond_in.icd10_code,
            onset_date=cond_in.onset_date,
            clinical_status=cond_in.clinical_status,
            raw_text=cond_in.raw_text,
            provenance_source=ProvenanceSourceEnum(cond_in.provenance_source.value),
            source_document=cond_in.source_document,
            source_page=cond_in.source_page,
            confidence=cond_in.confidence,
            source_snippet=cond_in.source_snippet,
            verification_status=VerificationStatusEnum(cond_in.verification_status.value),
            verified_by=cond_in.verified_by,
            verified_at=cond_in.verified_at,
        )
        self.db.add(db_cond)
        self.db.commit()
        self.db.refresh(db_cond)
        return db_cond

    def list_conditions_by_patient(self, patient_id: str) -> List[Condition]:
        return (
            self.db.query(Condition)
            .filter(Condition.patient_id == patient_id)
            .order_by(Condition.onset_date.desc().nullslast())
            .all()
        )

    # --- Allergies ---
    def add_allergy(self, allergy_in: AllergyCreate) -> Allergy:
        db_allergy = Allergy(
            patient_id=allergy_in.patient_id,
            document_id=allergy_in.document_id,
            page_id=allergy_in.page_id,
            allergen=allergy_in.allergen,
            reaction=allergy_in.reaction,
            severity=allergy_in.severity,
            raw_text=allergy_in.raw_text,
            provenance_source=ProvenanceSourceEnum(allergy_in.provenance_source.value),
            source_document=allergy_in.source_document,
            source_page=allergy_in.source_page,
            confidence=allergy_in.confidence,
            source_snippet=allergy_in.source_snippet,
            verification_status=VerificationStatusEnum(allergy_in.verification_status.value),
            verified_by=allergy_in.verified_by,
            verified_at=allergy_in.verified_at,
        )
        self.db.add(db_allergy)
        self.db.commit()
        self.db.refresh(db_allergy)
        return db_allergy

    def list_allergies_by_patient(self, patient_id: str) -> List[Allergy]:
        return self.db.query(Allergy).filter(Allergy.patient_id == patient_id).all()

    # --- Observations ---
    def add_observation(self, obs_in: ObservationCreate) -> Observation:
        db_obs = Observation(
            patient_id=obs_in.patient_id,
            document_id=obs_in.document_id,
            page_id=obs_in.page_id,
            observation_type=obs_in.observation_type,
            observation_name=obs_in.observation_name,
            numeric_value=obs_in.numeric_value,
            string_value=obs_in.string_value,
            unit=obs_in.unit,
            observation_date=obs_in.observation_date,
            provenance_source=ProvenanceSourceEnum(obs_in.provenance_source.value),
            source_document=obs_in.source_document,
            source_page=obs_in.source_page,
            confidence=obs_in.confidence,
            source_snippet=obs_in.source_snippet,
            verification_status=VerificationStatusEnum(obs_in.verification_status.value),
            verified_by=obs_in.verified_by,
            verified_at=obs_in.verified_at,
        )
        self.db.add(db_obs)
        self.db.commit()
        self.db.refresh(db_obs)
        return db_obs

    def list_observations_by_patient(self, patient_id: str) -> List[Observation]:
        return (
            self.db.query(Observation)
            .filter(Observation.patient_id == patient_id)
            .order_by(Observation.observation_date.desc().nullslast())
            .all()
        )
