from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import AuditLog
from app.schemas.audit import AuditLogCreate

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, audit_in: AuditLogCreate) -> AuditLog:
        db_log = AuditLog(
            entity_type=audit_in.entity_type,
            entity_id=audit_in.entity_id,
            action=audit_in.action,
            actor_id=audit_in.actor_id,
            actor_name=audit_in.actor_name,
            previous_state=audit_in.previous_state,
            new_state=audit_in.new_state,
            change_reason=audit_in.change_reason,
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    def list_by_entity(self, entity_type: str, entity_id: str) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )
