from abc import ABC, abstractmethod
from typing import Optional
from app.domain.camera.entities import Frame, CameraStatus


class ICameraAdapter(ABC):
    """
    Contrato que qualquer adaptador de câmera deve implementar.
    O domínio e a camada de aplicação dependem apenas desta interface,
    nunca da implementação concreta (OpenCV, GStreamer, etc).
    """

    @abstractmethod
    def start(self) -> None:
        """Inicia a captura da câmera. Lança CameraError se falhar."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Para a captura e libera recursos."""
        ...

    @abstractmethod
    def get_frame(self) -> Optional[Frame]:
        """
        Retorna o frame mais recente ou None se não houver frame disponível.
        Nunca bloqueia — retorno imediato.
        """
        ...

    @abstractmethod
    def get_status(self) -> CameraStatus:
        """Retorna o estado atual da câmera."""
        ...

    @abstractmethod
    def is_running(self) -> bool:
        """Retorna True se a câmera está capturando ativamente."""
        ...

    @abstractmethod
    def get_buffer_snapshot(self) -> Optional["VideoBuffer"]:
        """
        Retorna snapshot thread-safe do buffer circular atual.
        None se buffer vazio ou câmera parada.
        """
        ...


class IVideoWriter(ABC):
    """
    Contrato para qualquer implementação de escrita de vídeo.
    O domínio não sabe se usamos FFmpeg, OpenCV VideoWriter, etc.
    """

    @abstractmethod
    def write(
        self,
        frames: list,
        output_path: str,
        fps: float,
    ) -> tuple[str, float]:
        """
        Processa uma lista de frames e grava como vídeo.

        Args:
            frames: Lista de Frame objects com dados JPEG
            output_path: Caminho absoluto do arquivo de saída (.mp4)
            fps: Taxa de frames do vídeo de saída

        Returns:
            Tuple (caminho_absoluto_salvo, duracao_em_segundos)

        Raises:
            VideoWriteError: Se o processamento falhar por qualquer motivo
        """
        ...


class IJobStore(ABC):
    """
    Contrato para armazenamento de jobs de salvamento.
    No MVP: implementação em memória. Futuramente: Redis ou banco.
    """

    @abstractmethod
    def create(self, job: "SaveJob") -> None: ...

    @abstractmethod
    def get(self, job_id: str) -> Optional["SaveJob"]: ...

    @abstractmethod
    def update(self, job: "SaveJob") -> None: ...

    @abstractmethod
    def list_all(self) -> list["SaveJob"]: ...


class CameraError(Exception):
    """Erro base para falhas de câmera."""
    pass


class CameraNotFoundError(CameraError):
    """Câmera não encontrada no device index especificado."""
    pass


class CameraAlreadyRunningError(CameraError):
    """Tentativa de iniciar uma câmera já em execução."""
    pass


class VideoWriteError(Exception):
    """Erro durante processamento ou escrita de vídeo."""
    pass


class ITTLService(ABC):
    """
    Contrato para o serviço de limpeza automática de vídeos expirados.
    Implementação concreta fica em application/ttl/use_cases.py.
    """

    @abstractmethod
    def run_cleanup(self) -> "CleanupResult":
        """
        Executa limpeza completa de vídeos expirados e deletados.
        NUNCA lança exceção — todos os erros são capturados em CleanupResult.errors.
        Garante que o sistema continua funcionando mesmo se um arquivo não puder ser deletado.
        """
        ...

    @abstractmethod
    def get_last_result(self) -> Optional["CleanupResult"]:
        """
        Retorna o resultado da última execução bem-sucedida.
        Retorna None se o job nunca foi executado desde o início do servidor.
        """
        ...
