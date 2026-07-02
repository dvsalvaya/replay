import logging
import logging.handlers
import os
import sys
from app.config import settings


def setup_logging() -> None:
    """
    Configura o sistema de logging para todo o backend.
    Deve ser chamada UMA VEZ no startup da aplicação, antes de qualquer outro código.

    Configura dois handlers:
    - Console: INFO e acima, formato legível para desenvolvimento
    - Arquivo rotativo: DEBUG e acima, rastreamento completo em disco
    """
    os.makedirs(settings.log_dir, exist_ok=True)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Formato consistente para todos os logs
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler 1: Console (stdout) — INFO e acima
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Handler 2: Arquivo rotativo — DEBUG e acima
    log_file = os.path.join(settings.log_dir, "app.log")
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configurar logger raiz
    root_logger = logging.getLogger()
    # Limpa handlers anteriores do root_logger para evitar duplicações no reload
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG)  # captura tudo; handlers filtram por nível
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silenciar loggers verbosos de bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        f"Logging configurado: nível={settings.log_level}, arquivo={log_file}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Atalho para obter logger nomeado.
    Uso: logger = get_logger(__name__)
    """
    return logging.getLogger(name)
