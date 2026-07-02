from functools import lru_cache
from app.application.camera.use_cases import SaveMomentUseCase, InMemoryJobStore
from app.infrastructure.video.ffmpeg_writer import FFmpegWriter


@lru_cache(maxsize=1)
def get_job_store() -> InMemoryJobStore:
    return InMemoryJobStore()


@lru_cache(maxsize=1)
def get_save_moment_use_case() -> SaveMomentUseCase:
    return SaveMomentUseCase(
        writer=FFmpegWriter(),
        job_store=get_job_store(),
    )
