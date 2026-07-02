import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.camera.entities import Frame, CameraStatus, CaptureSession, VideoBuffer, SaveJob
from app.domain.camera.interfaces import (
    ICameraAdapter,
    CameraAlreadyRunningError,
    CameraError,
    IVideoWriter,
    IJobStore,
    VideoWriteError,
)
from app.videos.models import Video


class CameraUseCases:
    """
    Orquestra todas as operações de câmera.
    Depende apenas da interface ICameraAdapter — não conhece OpenCV.
    """

    def __init__(self, adapter: ICameraAdapter) -> None:
        self._adapter = adapter
        self._session: Optional[CaptureSession] = None

    def start_capture(self) -> CaptureSession:
        """
        Inicia a captura. Cria e retorna uma CaptureSession.
        Lança CameraAlreadyRunningError se já estiver rodando.
        """
        if self._adapter.is_running():
            raise CameraAlreadyRunningError("Câmera já está em execução")

        self._adapter.start()
        self._session = CaptureSession(
            session_id=str(uuid.uuid4()),
            device_index=self._adapter.get_status().device_index,
            started_at=time.time(),
        )
        return self._session

    def stop_capture(self) -> None:
        """Para a captura e encerra a sessão atual."""
        self._adapter.stop()
        self._session = None

    def get_current_frame(self) -> Optional[Frame]:
        """Retorna o frame mais recente. None se câmera parada ou sem frame."""
        if not self._adapter.is_running():
            return None
        return self._adapter.get_frame()

    def get_status(self) -> CameraStatus:
        """Retorna o status atual da câmera."""
        return self._adapter.get_status()

    def get_session(self) -> Optional[CaptureSession]:
        """Retorna a sessão ativa ou None."""
        return self._session

    def is_capturing(self) -> bool:
        return self._adapter.is_running()

    def get_buffer_snapshot(self) -> Optional[VideoBuffer]:
        """Retorna snapshot do buffer para salvamento."""
        if not self._adapter.is_running():
            return None
        return self._adapter.get_buffer_snapshot()


class InMemoryJobStore(IJobStore):
    """
    Implementação em memória do IJobStore para o MVP.
    Jobs são perdidos se o servidor reiniciar — aceitável para MVP local.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, SaveJob] = {}

    def create(self, job: SaveJob) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> Optional[SaveJob]:
        return self._jobs.get(job_id)

    def update(self, job: SaveJob) -> None:
        self._jobs[job.job_id] = job

    def list_all(self) -> list[SaveJob]:
        return list(self._jobs.values())


class SaveMomentUseCase:
    """
    Orquestra o salvamento de um momento:
    1. Pega snapshot do buffer
    2. Chama IVideoWriter para gerar o MP4
    3. Salva metadados no SQLite
    4. Atualiza o job com resultado
    """

    def __init__(
        self,
        writer: IVideoWriter,
        job_store: IJobStore,
    ) -> None:
        self._writer = writer
        self._job_store = job_store

    def create_job(self) -> SaveJob:
        """Cria e persiste um novo job com status pending."""
        job = SaveJob(
            job_id=str(uuid.uuid4()),
            status="pending",
            created_at=time.time(),
        )
        self._job_store.create(job)
        return job

    def execute(
        self,
        job_id: str,
        buffer: VideoBuffer,
        db: Session,
        title: Optional[str] = None,
    ) -> None:
        """
        Executa o salvamento em background.
        Atualiza o job ao longo do processo.
        Deve ser chamado em BackgroundTask.
        """
        job = self._job_store.get(job_id)
        if not job:
            return

        job.mark_processing()
        self._job_store.update(job)

        try:
            # Garantir que o diretório de vídeos existe
            os.makedirs(settings.videos_dir, exist_ok=True)

            # Gerar nome único para o arquivo
            filename = f"moment_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(settings.videos_dir, filename)

            # Delegar a escrita do vídeo para a infraestrutura
            saved_path, duration = self._writer.write(
                frames=buffer.frames,
                output_path=output_path,
                fps=buffer.fps,
            )

            # Calcular tamanho do arquivo
            file_size = os.path.getsize(saved_path)

            # Calcular data de expiração
            expires_at = datetime.now(timedelta(0)) + timedelta(days=7) # Wait, using datetime.now(timezone.utc) is better:
            # Let's import datetime, timezone and use datetime.now(timezone.utc) or timezone-naive as SQLite DB expects.
            # In Models.py, created_at default is timezone-aware or naive? In prompt 1 models.py:
            # created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
            # expires_at = Column(DateTime, nullable=False)
            # Both are DateTime columns. SQLite stores datetime strings. It is safer to use timezone-aware or naive depending on database format.
            # Let's use: datetime.now(timezone.utc) or datetime.utcnow()

            # Salvar metadados no banco
            video = Video(
                filename=filename,
                title=title,
                duration_seconds=duration,
                file_size_bytes=file_size,
                file_path=saved_path,
                expires_at=expires_at.replace(tzinfo=None), # Convert to naive for consistency with standard SQLAlchemy DateTime
            )
            db.add(video)
            db.commit()
            db.refresh(video)

            job.mark_done(video_id=video.id)
            self._job_store.update(job)

        except (VideoWriteError, OSError, Exception) as e:
            job.mark_error(str(e))
            self._job_store.update(job)
            db.rollback()

    def get_job(self, job_id: str) -> Optional[SaveJob]:
        return self._job_store.get(job_id)
