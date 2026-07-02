import logging
from fastapi import APIRouter, Depends, status
from app.admin.schemas import TTLStatusResponse, TTLRunResponse
from app.application.ttl.use_cases import ttl_use_case
from app.core.security import get_current_user
from app.infrastructure.scheduler.apscheduler import scheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ttl/status", response_model=TTLStatusResponse)
def get_ttl_status(_: str = Depends(get_current_user)):
    """
    Retorna estado atual do scheduler e resultado da última limpeza.
    Útil para verificar se o TTL está funcionando corretamente.
    """
    last = ttl_use_case.get_last_result()

    # Buscar próxima execução agendada
    next_run_at = None
    job = scheduler.get_job("ttl_cleanup")
    if job and job.next_run_time:
        next_run_at = job.next_run_time

    return TTLStatusResponse(
        scheduler_running=scheduler.running,
        next_run_at=next_run_at,
        last_run_at=last.started_at if last else None,
        last_duration_seconds=last.duration_seconds if last else None,
        last_videos_deleted=last.videos_deleted if last else None,
        last_files_deleted=last.files_deleted if last else None,
        last_files_missing=last.files_missing if last else None,
        last_temp_files_deleted=last.temp_files_deleted if last else None,
        last_mb_freed=last.mb_freed if last else None,
        last_had_errors=last.had_errors if last else None,
        last_errors=last.errors if last else None,
    )


@router.post("/ttl/run", response_model=TTLRunResponse, status_code=status.HTTP_200_OK)
def run_ttl_now(_: str = Depends(get_current_user)):
    """
    Executa o job de limpeza imediatamente, de forma síncrona.
    Use para testes e debugging — não interfere com o agendamento automático.
    """
    logger.info("TTL: execução manual disparada via /admin/ttl/run")
    result = ttl_use_case.run_cleanup()

    return TTLRunResponse(
        started_at=result.started_at,
        completed_at=result.completed_at,
        duration_seconds=result.duration_seconds,
        videos_deleted=result.videos_deleted,
        files_deleted=result.files_deleted,
        files_missing=result.files_missing,
        temp_files_deleted=result.temp_files_deleted,
        mb_freed=result.mb_freed,
        had_errors=result.had_errors,
        errors=result.errors,
    )
