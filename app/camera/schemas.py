from pydantic import BaseModel
from typing import Optional


class CameraStatusResponse(BaseModel):
    is_running: bool
    device_index: int
    fps: float
    resolution: tuple[int, int]
    error: Optional[str] = None
    is_healthy: bool


class CaptureSessionResponse(BaseModel):
    session_id: str
    device_index: int
    started_at: float
    frames_captured: int
    has_errors: bool


class MessageResponse(BaseModel):
    message: str
