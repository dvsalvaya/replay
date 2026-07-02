import collections
import threading
import time
from typing import Optional
import cv2
from app.config import settings
from app.core.logging_config import get_logger
from app.domain.camera.entities import Frame, CameraStatus, VideoBuffer
from app.domain.camera.interfaces import (
    ICameraAdapter,
    CameraNotFoundError,
)

logger = get_logger(__name__)


class OpenCVCameraAdapter(ICameraAdapter):
    """
    Implementação concreta de ICameraAdapter usando OpenCV.
    Captura frames em thread separada para não bloquear a API.
    """

    def __init__(self) -> None:
        self._cap: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[Frame] = None
        self._is_running: bool = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._error: Optional[str] = None
        self._device_index = settings.camera_device_index
        self._buffer: collections.deque = collections.deque(
            maxlen=settings.buffer_max_frames
        )

    def start(self) -> None:
        """Abre a câmera e inicia a thread de captura."""
        logger.info(f"Iniciando câmera no device index {self._device_index}")
        cap = cv2.VideoCapture(self._device_index)

        if not cap.isOpened():
            raise CameraNotFoundError(
                f"Câmera não encontrada no device index {self._device_index}"
            )

        cap.set(cv2.CAP_PROP_FPS, settings.camera_fps)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.camera_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.camera_height)

        self._cap = cap
        self._is_running = True
        self._error = None

        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="camera-capture-thread",
        )
        self._thread.start()
        logger.info("Câmera iniciada com sucesso")

    def stop(self) -> None:
        """Para a thread de captura e libera recursos."""
        logger.info("Parando a câmera...")
        self._is_running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        if self._cap:
            self._cap.release()
            self._cap = None

        with self._lock:
            self._latest_frame = None
            self._buffer.clear()
        logger.info("Câmera parada com sucesso")

    def get_frame(self) -> Optional[Frame]:
        """Retorna o frame mais recente de forma thread-safe."""
        with self._lock:
            return self._latest_frame

    def get_status(self) -> CameraStatus:
        actual_fps = 0.0
        resolution = (0, 0)

        if self._cap and self._cap.isOpened():
            actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            resolution = (w, h)

        return CameraStatus(
            is_running=self._is_running,
            device_index=self._device_index,
            fps=actual_fps,
            resolution=resolution,
            error=self._error,
        )

    def is_running(self) -> bool:
        return self._is_running

    def get_buffer_snapshot(self) -> Optional[VideoBuffer]:
        """
        Retorna um snapshot imutável do buffer atual.
        Thread-safe: copia os frames sob o lock.
        Retorna None se buffer vazio.
        """
        with self._lock:
            if not self._buffer:
                return None
            frames_copy = list(self._buffer)

        if not frames_copy:
            return None

        # Calcular duração real com base nos timestamps
        duration = frames_copy[-1].timestamp - frames_copy[0].timestamp
        fps = len(frames_copy) / duration if duration > 0 else settings.camera_fps

        return VideoBuffer(
            frames=frames_copy,
            captured_at=time.time(),
            duration_seconds=duration,
            fps=fps,
        )

    def _capture_loop(self) -> None:
        """
        Loop de captura rodando em thread separada.
        Captura frames continuamente e atualiza _latest_frame e _buffer.
        Todos os erros são logados e refletidos no status da câmera.
        A thread nunca termina silenciosamente.
        """
        logger.info(f"Thread de captura iniciada (device={self._device_index})")
        interval = 1.0 / settings.camera_fps
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 10

        while self._is_running:
            start = time.monotonic()

            try:
                if not self._cap or not self._cap.isOpened():
                    raise RuntimeError("Câmera desconectada durante captura")

                ret, raw_frame = self._cap.read()

                if not ret:
                    consecutive_errors += 1
                    logger.warning(
                        f"Falha ao ler frame (tentativa {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})"
                    )
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        raise RuntimeError(
                            f"Câmera falhou {MAX_CONSECUTIVE_ERRORS} vezes consecutivas"
                        )
                    time.sleep(interval)
                    continue

                # Frame lido com sucesso — resetar contador de erros
                consecutive_errors = 0

                encode_params = [cv2.IMWRITE_JPEG_QUALITY, settings.camera_jpeg_quality]
                success, buffer = cv2.imencode(".jpg", raw_frame, encode_params)

                if not success:
                    logger.warning("Falha ao encodar frame como JPEG — frame descartado")
                    continue

                frame = Frame(
                    data=buffer.tobytes(),
                    width=raw_frame.shape[1],
                    height=raw_frame.shape[0],
                    timestamp=time.time(),
                )

                with self._lock:
                    self._latest_frame = frame
                    self._buffer.append(frame)

            except Exception as e:
                # Captura qualquer erro não previsto — loga e encerra a thread com segurança
                error_msg = f"Erro crítico na thread de captura: {e}"
                logger.error(error_msg, exc_info=True)
                with self._lock:
                    self._error = error_msg
                self._is_running = False
                break

            # Controle de FPS
            elapsed = time.monotonic() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        logger.info("Thread de captura encerrada")
