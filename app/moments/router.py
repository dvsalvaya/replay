from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.application.camera.use_cases import CameraUseCases, SaveMomentUseCase
from app.camera.dependencies import get_camera_use_cases
from app.core.security import get_current_user
from app.database import get_db
from app.moments.dependencies import get_save_moment_use_case
from app.moments.schemas import (
    SaveMomentRequest,
    SaveMomentResponse,
    JobStatusResponse,
)

router = APIRouter(prefix="/moments", tags=["moments"])


@router.post("/save", response_model=SaveMomentResponse)
def save_moment(
    request: SaveMomentRequest,
    background_tasks: BackgroundTasks,
    camera: CameraUseCases = Depends(get_camera_use_cases),
    use_case: SaveMomentUseCase = Depends(get_save_moment_use_case),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """
    Salva os últimos N segundos do buffer como MP4.
    Retorna imediatamente com job_id para polling.
    """
    if not camera.is_capturing():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Câmera não está em execução. Inicie a câmera antes de salvar.",
        )

    buffer = camera.get_buffer_snapshot()
    if not buffer or buffer.frame_count == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Buffer vazio. Aguarde alguns segundos após iniciar a câmera.",
        )

    # Criar job antes de disparar background task
    job = use_case.create_job()

    # Disparar processamento em background (não bloqueia a resposta)
    background_tasks.add_task(
        use_case.execute,
        job_id=job.job_id,
        buffer=buffer,
        db=db,
        title=request.title,
    )

    return SaveMomentResponse(
        job_id=job.job_id,
        status="pending",
        message=f"Processando {buffer.frame_count} frames ({buffer.duration_seconds:.1f}s de vídeo)",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    use_case: SaveMomentUseCase = Depends(get_save_moment_use_case),
    _: str = Depends(get_current_user),
):
    """Retorna o status atual de um job de salvamento."""
    job = use_case.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado",
        )

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        video_id=job.video_id,
        error_message=job.error_message,
        completed_at=job.completed_at,
    )
