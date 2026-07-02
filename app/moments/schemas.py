from pydantic import BaseModel
from typing import Literal, Optional


class SaveMomentRequest(BaseModel):
    title: Optional[str] = None


class SaveMomentResponse(BaseModel):
    job_id: str
    status: Literal["pending"]
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "done", "error"]
    video_id: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[float] = None
