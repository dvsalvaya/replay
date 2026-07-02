import logging
import os
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.domain.camera.entities import CleanupResult
from app.domain.camera.interfaces import ITTLService
from app.videos.models import Video

logger = logging.getLogger(__name__)


class CleanExpiredVideosUseCase(ITTLService):
    """
    Executa a limpeza de vídeos expirados ou deletados manualmente.

    Candidatos à limpeza:
    - Vídeos com expires_at < datetime.utcnow()  ← TTL natural atingido
    - Vídeos com is_deleted=True                 ← deletados manualmente na galeria

    Para cada candidato:
    1. Tenta apagar o arquivo físico do disco
    2. Remove o registro do banco (hard delete)
    3. Registra erro sem interromper o loop se qualquer passo falhar

    Também limpa arquivos órfãos em storage/temp/ com mais de TTL_TEMP_MAX_AGE_HOURS.
    """

    def __init__(self) -> None:
        self._last_result: CleanupResult | None = None

    def run_cleanup(self) -> CleanupResult:
        """
        Ponto de entrada principal. Cria sua própria Session para poder rodar
        fora do contexto de uma requisição HTTP (dentro do scheduler).
        """
        started_at = time.time()
        videos_deleted = 0
        files_deleted = 0
        files_missing = 0
        temp_files_deleted = 0
        bytes_freed = 0
        errors: list[str] = []

        logger.info("TTL cleanup iniciado")

        db: Session = SessionLocal()
        try:
            # 1. Buscar candidatos: expirados OU deletados manualmente
            candidates = (
                db.query(Video)
                .filter(
                    (Video.expires_at < datetime.utcnow())
                    | (Video.is_deleted == True)
                )
                .all()
            )

            logger.info(f"TTL: {len(candidates)} vídeo(s) candidato(s) à limpeza")

            # 2. Processar cada candidato
            for video in candidates:
                try:
                    file_size = 0

                    # Apagar arquivo físico se existir
                    if os.path.exists(video.file_path):
                        file_size = os.path.getsize(video.file_path)
                        os.remove(video.file_path)
                        files_deleted += 1
                        bytes_freed += file_size
                        logger.debug(f"TTL: arquivo removido: {video.file_path}")
                    else:
                        files_missing += 1
                        logger.warning(
                            f"TTL: arquivo não encontrado no disco: {video.file_path}"
                        )

                    # Remover registro do banco (hard delete)
                    db.delete(video)
                    db.flush()
                    videos_deleted += 1

                except OSError as e:
                    error_msg = f"Erro ao remover arquivo {video.file_path}: {e}"
                    errors.append(error_msg)
                    logger.error(f"TTL: {error_msg}")
                    # Continua o loop — não aborta por erro em um arquivo

            db.commit()

            # 3. Limpar arquivos temporários órfãos
            temp_result = self._cleanup_temp_dir()
            temp_files_deleted = temp_result["deleted"]
            bytes_freed += temp_result["bytes_freed"]
            errors.extend(temp_result["errors"])

        except Exception as e:
            db.rollback()
            error_msg = f"Erro crítico durante TTL cleanup: {e}"
            errors.append(error_msg)
            logger.exception(f"TTL: {error_msg}")
        finally:
            db.close()

        result = CleanupResult(
            started_at=started_at,
            completed_at=time.time(),
            videos_deleted=videos_deleted,
            files_deleted=files_deleted,
            files_missing=files_missing,
            temp_files_deleted=temp_files_deleted,
            bytes_freed=bytes_freed,
            errors=errors,
        )

        self._last_result = result
        logger.info(result.to_log_line())
        return result

    def get_last_result(self) -> CleanupResult | None:
        return self._last_result

    def _cleanup_temp_dir(self) -> dict:
        """
        Remove arquivos órfãos em storage/temp/ com mais de TTL_TEMP_MAX_AGE_HOURS.
        Esses arquivos são resíduos de jobs de FFmpeg que falharam ou travaram.
        """
        deleted = 0
        bytes_freed = 0
        errors: list[str] = []
        temp_dir = settings.temp_dir
        max_age = timedelta(hours=settings.ttl_temp_max_age_hours)
        cutoff = datetime.utcnow() - max_age

        if not os.path.exists(temp_dir):
            return {"deleted": 0, "bytes_freed": 0, "errors": []}

        try:
            for entry in os.scandir(temp_dir):
                try:
                    modified = datetime.fromtimestamp(entry.stat().st_mtime)
                    if modified < cutoff:
                        size = entry.stat().st_size
                        if entry.is_file():
                            os.remove(entry.path)
                        elif entry.is_dir():
                            import shutil
                            shutil.rmtree(entry.path, ignore_errors=True)
                        deleted += 1
                        bytes_freed += size
                        logger.debug(f"TTL: temp órfão removido: {entry.path}")
                except OSError as e:
                    errors.append(f"Erro ao remover temp {entry.path}: {e}")
        except OSError as e:
            errors.append(f"Erro ao escanear diretório temp {temp_dir}: {e}")

        return {"deleted": deleted, "bytes_freed": bytes_freed, "errors": errors}


# Singleton — uma única instância durante o ciclo de vida da aplicação
ttl_use_case = CleanExpiredVideosUseCase()
