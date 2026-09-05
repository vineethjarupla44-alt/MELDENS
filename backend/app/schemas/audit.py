from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuditLogBase(BaseModel):
    entity_type: str
    entity_id: str
    action: str = Field(..., description="CREATE, UPDATE, VERIFY, RESOLVE_CONFLICT, DELETE")
    actor_id: str = "SYSTEM"
    actor_name: str = "System Engine"
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    change_reason: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogRead(AuditLogBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True
