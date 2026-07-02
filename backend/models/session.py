from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SessionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class PipelineMetadata(BaseModel):
    """Session manifest persisted to B2 (ADR-008: B2 is the source of truth).

    Self-contained: holds everything RecapResponse needs so GET /recap/{id}
    can be served from B2 alone when the SQLite cache is missing (redeploy).
    """

    session_id: str
    user_id: str
    status: str = "complete"
    created_at: datetime
    pipeline_version: str
    genblaze_version: str = "0.2.4"
    models_used: dict[str, str]
    input_filename: str
    input_hash: str
    output_url: str = ""
    processing_time_ms: int = 0
    synthetic_data: bool = False
    insights: dict = {}  # InsightsSummary-shaped snapshot
    b2_keys: dict[str, str] = {}


class Session(BaseModel):
    session_id: str
    user_id: str
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime
    updated_at: datetime
    output_url: str = ""
    metadata: dict = {}
    error: str = ""
