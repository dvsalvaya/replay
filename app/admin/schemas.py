from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TTLStatusResponse(BaseModel):
    scheduler_running: bool
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[float] = None
    last_duration_seconds: Optional[float] = None
    last_videos_deleted: Optional[int] = None
    last_files_deleted: Optional[int] = None
    last_files_missing: Optional[int] = None
    last_temp_files_deleted: Optional[int] = None
    last_mb_freed: Optional[float] = None
    last_had_errors: Optional[bool] = None
    last_errors: Optional[list[str]] = None


class TTLRunResponse(BaseModel):
    started_at: float
    completed_at: float
    duration_seconds: float
    videos_deleted: int
    files_deleted: int
    files_missing: int
    temp_files_deleted: int
    mb_freed: float
    had_errors: bool
    errors: list[str]
