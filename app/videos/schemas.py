from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional


class VideoResponse(BaseModel):
    id: int
    filename: str
    title: Optional[str]
    duration_seconds: float
    file_size_bytes: int
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def days_until_expiry(self) -> int:
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    @computed_field
    @property
    def is_expiring_soon(self) -> bool:
        return self.days_until_expiry <= 2


class VideoListResponse(BaseModel):
    items: list[VideoResponse]
    total: int
    page: int
    page_size: int
