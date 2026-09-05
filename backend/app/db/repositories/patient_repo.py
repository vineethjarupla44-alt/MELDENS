from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.db.models import Patient, PatientProfile
from app.schemas.patient import PatientCreate, PatientProfileCreate

class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, patient_in: PatientCreate) -> Patient:
        db_patient = Patient(
            mrn=patient_in.mrn,
            first_name=patient_in.first_name,
            last_name=patient_in.last_name,
            date_of_birth=patient_in.date_of_birth,
            gender=patient_in.gender,
            blood_type=patient_in.blood_type,
        )
        self.db.add(db_patient)
        self.db.flush()

        if patient_in.profile:
            db_profile = PatientProfile(
                patient_id=db_patient.id,
                emergency_contact_name=patient_in.profile.emergency_contact_name,
                emergency_contact_phone=patient_in.profile.emergency_contact_phone,
                preferred_language=patient_in.profile.preferred_language,
                insurance_provider=patient_in.profile.insurance_provider,
                baseline_notes=patient_in.profile.baseline_notes,
            )
            self.db.add(db_profile)

        self.db.commit()
        self.db.refresh(db_patient)
        return db_patient

    def get_by_id(self, patient_id: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.id == patient_id).first()

    def get_by_mrn(self, mrn: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.mrn == mrn).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        return self.db.query(Patient).offset(skip).limit(limit).all()

    def get_detail(self, patient_id: str) -> Optional[Patient]:
        return (
            self.db.query(Patient)
            .options(
                joinedload(Patient.profile),
                joinedload(Patient.documents),
                joinedload(Patient.lab_results),
                joinedload(Patient.medications),
                joinedload(Patient.conditions),
                joinedload(Patient.allergies),
                joinedload(Patient.observations),
            )
            .filter(Patient.id == patient_id)
            .first()
        )
