from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DATABASE_URL: str
    VIDEOS_DIR: str
    camera_device_index: int = 0
    camera_fps: int = 15
    camera_width: int = 1280
    camera_height: int = 720
    camera_jpeg_quality: int = 70
    buffer_duration_seconds: int = 120
    buffer_max_frames: int = 1800
    temp_dir: str = "./storage/temp"
    ffmpeg_path: str = "ffmpeg"
    ffmpeg_crf: int = 23
    ffmpeg_preset: str = "ultrafast"
    ttl_days: int = 7
    ttl_run_interval_hours: int = 1
    ttl_temp_max_age_hours: int = 24
    log_level: str = "INFO"
    log_dir: str = "./logs"
    log_max_bytes: int = 10_485_760   # 10 MB
    log_backup_count: int = 5

    @property
    def videos_dir(self) -> str:
        return self.VIDEOS_DIR

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
