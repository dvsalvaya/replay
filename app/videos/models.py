import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    expires_at = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False)
