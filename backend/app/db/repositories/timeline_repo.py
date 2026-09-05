from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import TimelineEvent
from app.schemas.timeline import TimelineEventCreate

class TimelineRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_event(self, event_in: TimelineEventCreate) -> TimelineEvent:
        db_event = TimelineEvent(
            patient_id=event_in.patient_id,
            event_date=event_in.event_date,
            event_type=event_in.event_type,
            title=event_in.title,
            description=event_in.description,
            entity_type=event_in.entity_type,
            entity_id=event_in.entity_id,
            source_document=event_in.source_document,
            source_page=event_in.source_page,
            importance=event_in.importance,
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def list_by_patient(self, patient_id: str) -> List[TimelineEvent]:
        return (
            self.db.query(TimelineEvent)
            .filter(TimelineEvent.patient_id == patient_id)
            .order_by(TimelineEvent.event_date.asc())
            .all()
        )
