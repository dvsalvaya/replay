import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.application.ttl.use_cases import ttl_use_case
from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _run_ttl_job() -> None:
    """
    Wrapper do job de TTL para o APScheduler.
    NUNCA propaga exceções — o APScheduler não deve saber de falhas internas.
    Todos os erros são logados e refletidos no CleanupResult.
    """
    logger.info("Scheduler: iniciando job de limpeza TTL")

    try:
        result = ttl_use_case.run_cleanup()

        if result.videos_deleted > 0 or result.files_deleted > 0:
            logger.info(
                f"Scheduler: TTL concluído — {result.videos_deleted} vídeo(s) removidos, "
                f"{result.mb_freed:.1f} MB liberados em {result.duration_seconds:.2f}s"
            )
        else:
            logger.info(
                f"Scheduler: TTL concluído — nenhum vídeo expirado "
                f"({result.duration_seconds:.2f}s)"
            )

        if result.had_errors:
            logger.warning(
                f"Scheduler: TTL concluído com {len(result.errors)} erro(s): "
                f"{'; '.join(result.errors[:3])}"
            )

    except Exception as e:
        # Captura qualquer exceção inesperada fora do CleanupResult
        # O APScheduler não recebe a exceção — o job será reagendado normalmente
        logger.critical(
            f"Scheduler: erro inesperado e não tratado no job TTL: {e}",
            exc_info=True,
        )


def create_scheduler() -> BackgroundScheduler:
    """
    Cria e configura o scheduler com o job de TTL.
    NÃO inicia o scheduler — isso é feito no lifespan do FastAPI.
    """
    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,       # se perdeu execuções, roda apenas uma vez
            "max_instances": 1,     # nunca roda duas limpezas simultaneamente
            "misfire_grace_time": 300,  # tolera até 5 min de atraso
        }
    )

    scheduler.add_job(
        func=_run_ttl_job,
        trigger=IntervalTrigger(hours=settings.ttl_run_interval_hours),
        id="ttl_cleanup",
        name="Limpeza de vídeos expirados",
        replace_existing=True,
    )

    logger.info(
        f"Scheduler configurado: job TTL a cada {settings.ttl_run_interval_hours}h"
    )
    return scheduler


# Instância global — acessada pelo lifespan e pelo router de admin
scheduler = create_scheduler()
