from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class Frame:
    """Representa um frame capturado da câmera, já encodado em JPEG."""
    data: bytes
    width: int
    height: int
    timestamp: float

    def __post_init__(self) -> None:
        if not self.data:
            raise ValueError("Frame data não pode ser vazio")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Dimensões do frame devem ser positivas")


@dataclass
class CameraStatus:
    """Estado atual da câmera."""
    is_running: bool
    device_index: int
    fps: float
    resolution: tuple[int, int]
    error: Optional[str] = None

    @property
    def is_healthy(self) -> bool:
        return self.is_running and self.error is None


@dataclass
class CaptureSession:
    """Representa uma sessão de captura ativa."""
    session_id: str
    device_index: int
    started_at: float
    frames_captured: int = 0
    errors: list[str] = field(default_factory=list)

    def record_frame(self) -> None:
        self.frames_captured += 1

    def record_error(self, error: str) -> None:
        self.errors.append(error)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


@dataclass
class VideoBuffer:
    """
    Snapshot imutável do conteúdo do buffer circular no momento do salvamento.
    Criado quando o usuário clica 'Salvar Momento'.
    """
    frames: list["Frame"]
    captured_at: float
    duration_seconds: float
    fps: float

    def __post_init__(self) -> None:
        if not self.frames:
            raise ValueError("VideoBuffer não pode ter lista de frames vazia")
        if self.fps <= 0:
            raise ValueError("FPS deve ser positivo")

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def estimated_size_bytes(self) -> int:
        return sum(len(f.data) for f in self.frames)


@dataclass
class SaveJob:
    """
    Representa um job assíncrono de salvamento de vídeo.
    Criado imediatamente ao receber o request de salvar.
    Atualizado quando o processamento termina (sucesso ou erro).
    """
    job_id: str
    status: Literal["pending", "processing", "done", "error"]
    created_at: float
    completed_at: Optional[float] = None
    video_id: Optional[int] = None
    error_message: Optional[str] = None

    def mark_processing(self) -> None:
        self.status = "processing"

    def mark_done(self, video_id: int) -> None:
        import time
        self.status = "done"
        self.video_id = video_id
        self.completed_at = time.time()

    def mark_error(self, message: str) -> None:
        import time
        self.status = "error"
        self.error_message = message
        self.completed_at = time.time()

    @property
    def is_terminal(self) -> bool:
        return self.status in ("done", "error")


@dataclass
class CleanupResult:
    """
    Resultado de uma execução do job de limpeza de vídeos expirados.
    Imutável após criação — representa um snapshot do que aconteceu.
    """
    started_at: float
    completed_at: float
    videos_deleted: int
    files_deleted: int
    files_missing: int
    temp_files_deleted: int
    bytes_freed: int
    errors: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return self.completed_at - self.started_at

    @property
    def mb_freed(self) -> float:
        return round(self.bytes_freed / (1024 * 1024), 2)

    @property
    def had_errors(self) -> bool:
        return len(self.errors) > 0

    def to_log_line(self) -> str:
        """Formata resultado como linha de log legível."""
        return (
            f"TTL cleanup concluído em {self.duration_seconds:.2f}s: "
            f"{self.videos_deleted} vídeos removidos, "
            f"{self.files_deleted} arquivos deletados, "
            f"{self.mb_freed:.1f} MB liberados"
            + (f", {len(self.errors)} erros" if self.had_errors else "")
        )

