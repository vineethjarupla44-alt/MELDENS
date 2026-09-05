import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import (
    Patient,
    PatientProfile,
    Condition,
    Allergy,
    Medication,
    TimelineEvent,
    AuditLog,
    ProvenanceSourceEnum,
    VerificationStatusEnum,
)
from app.schemas.intake import PatientIntakeSubmission, PatientIntakeResponse

class IntakeService:
    def __init__(self, db: Session):
        self.db = db

    def submit_intake(self, intake: PatientIntakeSubmission, actor_name: str = "Patient Intake Portal") -> PatientIntakeResponse:
        """
        Creates a patient record from intake.
        All clinical facts are stamped with PATIENT_INPUT provenance.
        Logs an immutable AuditLog record.
        """
        # 1. Generate unique MRN if omitted
        mrn = intake.mrn
        if not mrn:
            mrn = f"MED-IN-{uuid.uuid4().hex[:6].upper()}"

        # 2. Patient Demographics
        patient = Patient(
            id=str(uuid.uuid4()),
            mrn=mrn,
            first_name=intake.first_name.strip(),
            last_name=intake.last_name.strip(),
            date_of_birth=intake.date_of_birth,
            gender=intake.gender,
            blood_type=intake.blood_type,
        )
        self.db.add(patient)
        self.db.flush()

        # 3. Patient Profile with Symptoms & Baseline Notes
        profile = PatientProfile(
            patient_id=patient.id,
            emergency_contact_name=intake.emergency_contact_name,
            emergency_contact_phone=intake.emergency_contact_phone,
            preferred_language=intake.preferred_language,
            symptoms=intake.symptoms,
            baseline_notes=intake.additional_notes,
        )
        self.db.add(profile)

        # 4. Conditions (Provenance: PATIENT_INPUT)
        for cond in intake.existing_conditions:
            db_cond = Condition(
                patient_id=patient.id,
                condition_name=cond.condition_name.strip(),
                onset_date=cond.onset_date,
                clinical_status=cond.clinical_status,
                provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
                source_document="Patient Intake Portal",
                source_page=1,
                confidence=1.0,
                source_snippet=f"Patient self-reported: {cond.condition_name}",
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_cond)

        # 5. Allergies (Provenance: PATIENT_INPUT)
        for al in intake.allergies:
            db_al = Allergy(
                patient_id=patient.id,
                allergen=al.allergen.strip(),
                reaction=al.reaction,
                severity=al.severity,
                provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
                source_document="Patient Intake Portal",
                source_page=1,
                confidence=1.0,
                source_snippet=f"Patient self-reported: {al.allergen} ({al.reaction or 'Reaction not specified'})",
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_al)

        # 6. Medications (Provenance: PATIENT_INPUT)
        for med in intake.current_medications:
            db_med = Medication(
                patient_id=patient.id,
                medication_name=med.medication_name.strip(),
                dosage=med.dosage,
                frequency=med.frequency,
                route=med.route,
                clinical_status="ACTIVE",
                provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
                source_document="Patient Intake Portal",
                source_page=1,
                confidence=1.0,
                source_snippet=f"Patient self-reported: {med.medication_name} {med.dosage or ''} {med.frequency or ''}",
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_med)

        # 7. Timeline Event
        event = TimelineEvent(
            patient_id=patient.id,
            event_date=datetime.utcnow().strftime("%Y-%m-%d"),
            event_type="ENCOUNTER",
            title="Patient Self-Assessment Intake Form Completed",
            description=f"Self-reported intake: {len(intake.existing_conditions)} conditions, {len(intake.allergies)} allergies, {len(intake.current_medications)} medications.",
            source_document="Patient Intake Portal",
            source_page=1,
            importance="ROUTINE",
        )
        self.db.add(event)

        # 8. Immutable Audit Log
        audit_state = {
            "mrn": mrn,
            "name": f"{patient.first_name} {patient.last_name}",
            "dob": patient.date_of_birth,
            "gender": patient.gender,
            "symptoms": intake.symptoms,
            "conditions": [c.condition_name for c in intake.existing_conditions],
            "allergies": [a.allergen for a in intake.allergies],
            "medications": [m.medication_name for m in intake.current_medications],
        }
        audit = AuditLog(
            entity_type="Patient",
            entity_id=patient.id,
            action="CREATE",
            actor_id="PATIENT_PORTAL",
            actor_name=actor_name,
            new_state=json.dumps(audit_state),
            change_reason="Initial patient self-assessment intake submission",
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(patient)

        return PatientIntakeResponse(
            patient_id=patient.id,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_type=patient.blood_type,
            symptoms=intake.symptoms,
            additional_notes=intake.additional_notes,
            provenance_source="PATIENT_INPUT",
            conditions_count=len(intake.existing_conditions),
            allergies_count=len(intake.allergies),
            medications_count=len(intake.current_medications),
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            audit_id=audit.id,
        )

    def update_intake(
        self, 
        patient_id: str, 
        intake: PatientIntakeSubmission, 
        actor_name: str = "Patient Portal User",
        change_reason: str = "Patient intake updated"
    ) -> Optional[PatientIntakeResponse]:
        """
        Updates an existing patient intake, preserving complete audit trail.
        """
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None

        # Capture previous state for audit log
        previous_state = {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "dob": patient.date_of_birth,
            "gender": patient.gender,
            "blood_type": patient.blood_type,
            "symptoms": patient.profile.symptoms if patient.profile else None,
            "additional_notes": patient.profile.baseline_notes if patient.profile else None,
        }

        # Update Demographics
        patient.first_name = intake.first_name.strip()
        patient.last_name = intake.last_name.strip()
        patient.date_of_birth = intake.date_of_birth
        patient.gender = intake.gender
        if intake.blood_type:
            patient.blood_type = intake.blood_type
        patient.updated_at = datetime.utcnow()

        # Update Profile
        if not patient.profile:
            patient.profile = PatientProfile(patient_id=patient.id)
            self.db.add(patient.profile)

        patient.profile.symptoms = intake.symptoms
        patient.profile.baseline_notes = intake.additional_notes
        if intake.emergency_contact_name:
            patient.profile.emergency_contact_name = intake.emergency_contact_name
        if intake.emergency_contact_phone:
            patient.profile.emergency_contact_phone = intake.emergency_contact_phone
        if intake.preferred_language:
            patient.profile.preferred_language = intake.preferred_language
        patient.profile.updated_at = datetime.utcnow()

        # Replace or append patient-input conditions
        # We only touch conditions whose provenance_source == PATIENT_INPUT
        self.db.query(Condition).filter(
            Condition.patient_id == patient.id,
            Condition.provenance_source == ProvenanceSourceEnum.PATIENT_INPUT
        ).delete()
        for cond in intake.existing_conditions:
            db_cond = Condition(
                patient_id=patient.id,
                condition_name=cond.condition_name.strip(),
                onset_date=cond.onset_date,
                clinical_status=cond.clinical_status,
                provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
                source_document="Patient Intake Portal",
                source_page=1,
                confidence=1.0,
                source_snippet=f"Patient self-reported (updated): {cond.condition_name}",
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_cond)

        # Replace or append patient-input allergies
        self.db.query(Allergy).filter(
            Allergy.patient_id == patient.id,
            Allergy.provenance_source == ProvenanceSourceEnum.PATIENT_INPUT
        ).delete()
        for al in intake.allergies:
            db_al = Allergy(
                patient_id=patient.id,
                allergen=al.allergen.strip(),
                reaction=al.reaction,
                severity=al.severity,
                provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
                source_document="Patient Intake Portal",
                source_page=1,
                confidence=1.0,
                source_snippet=f"Patient self-reported (updated): {al.allergen}",
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_al)

        # Replace or append patient-input medications
        self.db.query(Medication).filter(
            Medication.patient_id == patient.id,
            Medication.provenance_source == ProvenanceSourceEnum.PATIENT_INPUT
        ).delete()
        for med in intake.current_medications:
            db_med = Medication(
                patient_id=patient.id,
                medication_name=med.medication_name.strip(),
                dosage=med.dosage,
                frequency=med.frequency,
                route=med.route,
                clinical_status="ACTIVE",
                provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
                source_document="Patient Intake Portal",
                source_page=1,
                confidence=1.0,
                source_snippet=f"Patient self-reported (updated): {med.medication_name}",
                verification_status=VerificationStatusEnum.UNVERIFIED,
            )
            self.db.add(db_med)

        new_state = {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "dob": patient.date_of_birth,
            "gender": patient.gender,
            "blood_type": patient.blood_type,
            "symptoms": patient.profile.symptoms,
            "conditions": [c.condition_name for c in intake.existing_conditions],
            "allergies": [a.allergen for a in intake.allergies],
            "medications": [m.medication_name for m in intake.current_medications],
        }

        # Audit Log Entry
        audit = AuditLog(
            entity_type="Patient",
            entity_id=patient.id,
            action="UPDATE",
            actor_id="PATIENT_PORTAL",
            actor_name=actor_name,
            previous_state=json.dumps(previous_state),
            new_state=json.dumps(new_state),
            change_reason=change_reason,
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(patient)

        return PatientIntakeResponse(
            patient_id=patient.id,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_type=patient.blood_type,
            symptoms=patient.profile.symptoms,
            additional_notes=patient.profile.baseline_notes,
            provenance_source="PATIENT_INPUT",
            conditions_count=len(intake.existing_conditions),
            allergies_count=len(intake.allergies),
            medications_count=len(intake.current_medications),
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            audit_id=audit.id,
        )
