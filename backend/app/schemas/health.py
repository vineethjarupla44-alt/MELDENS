from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any

class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="System operational status")
    service: str = Field(default="MedLens Backend", description="Service name")
    version: str = Field(default="1.0.0-phase1", description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current server UTC timestamp")
    environment: str = Field(default="development", description="Current execution environment")
    database: str = Field(default="connected", description="Database connectivity status")
    system_capabilities: Dict[str, Any] = Field(
        default_factory=lambda: {
            "document_processing": "ready",
            "reference_range_validation": "deterministic_only",
            "conflict_detection": "ready",
            "provenance_tracking": "enabled"
        }
    )
