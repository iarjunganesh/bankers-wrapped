from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class PipelineMetadata(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    pipeline_version: str
    genblaze_version: str = "0.2.4"
    models_used: dict[str, str]
    input_filename: str
    input_hash: str
    output_url: str = ""
    processing_time_ms: int = 0
    synthetic_data: bool = False


class Session(BaseModel):
    session_id: str
    user_id: str
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime
    updated_at: datetime
    output_url: str = ""
    metadata: dict = {}
    error: str = ""
