from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.models import ConflictRecord, ConflictStatusEnum, ConflictCategoryEnum
from app.schemas.conflict import ConflictRecordCreate, ConflictResolveRequest

class ConflictRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_conflict(self, conflict_in: ConflictRecordCreate) -> ConflictRecord:
        db_conflict = ConflictRecord(
            patient_id=conflict_in.patient_id,
            category=ConflictCategoryEnum(conflict_in.category.value),
            field_name=conflict_in.field_name,
            source_a_type=conflict_in.source_a_type,
            source_a_document=conflict_in.source_a_document,
            source_a_page=conflict_in.source_a_page,
            source_a_value=conflict_in.source_a_value,
            source_b_type=conflict_in.source_b_type,
            source_b_document=conflict_in.source_b_document,
            source_b_page=conflict_in.source_b_page,
            source_b_value=conflict_in.source_b_value,
            description=conflict_in.description,
            severity=conflict_in.severity,
            status=ConflictStatusEnum(conflict_in.status.value),
        )
        self.db.add(db_conflict)
        self.db.commit()
        self.db.refresh(db_conflict)
        return db_conflict

    def list_by_patient(self, patient_id: str, status: Optional[str] = None) -> List[ConflictRecord]:
        query = self.db.query(ConflictRecord).filter(ConflictRecord.patient_id == patient_id)
        if status:
            query = query.filter(ConflictRecord.status == status)
        return query.order_by(ConflictRecord.created_at.desc()).all()

    def list_all(self, status: Optional[str] = None) -> List[ConflictRecord]:
        query = self.db.query(ConflictRecord)
        if status:
            query = query.filter(ConflictRecord.status == status)
        return query.order_by(ConflictRecord.created_at.desc()).all()

    def resolve(self, conflict_id: str, resolve_in: ConflictResolveRequest) -> Optional[ConflictRecord]:
        conflict = self.db.query(ConflictRecord).filter(ConflictRecord.id == conflict_id).first()
        if not conflict:
            return None
        conflict.status = ConflictStatusEnum(resolve_in.status.value)
        conflict.resolution_notes = resolve_in.resolution_notes
        conflict.resolved_by = resolve_in.resolved_by
        conflict.resolved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conflict)
        return conflict
