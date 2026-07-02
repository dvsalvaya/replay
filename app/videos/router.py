import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.core.security import get_current_user, verify_token
from app.database import get_db
from app.videos.schemas import VideoListResponse, VideoResponse
from app.videos.service import video_service

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/", response_model=VideoListResponse)
def list_videos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Lista todos os vídeos ativos, ordenados por data de criação."""
    items, total = video_service.list_active(db, page=page, page_size=page_size)
    return VideoListResponse(
        items=[VideoResponse.model_validate(v) for v in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{video_id}/stream")
def stream_video(
    video_id: int,
    token: str = Query(..., description="JWT token para autenticação"),
    db: Session = Depends(get_db),
):
    """
    Serve o arquivo MP4 para reprodução no player HTML5.
    Autenticação via query param porque <video src> não suporta headers customizados.
    """
    # Validar token manualmente (não usa Depends pois vem via query param)
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    username = payload.get("sub")
    if not username or not secrets.compare_digest(username, settings.ADMIN_USERNAME):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    video = video_service.get_active_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vídeo não encontrado",
        )

    if not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo de vídeo não encontrado no disco",
        )

    return FileResponse(
        path=video.file_path,
        media_type="video/mp4",
        filename=video.filename,
        headers={
            "Accept-Ranges": "bytes",               # habilita seeking no player
            "Cache-Control": "no-cache",            # sem cache no MVP local
        },
    )


@router.delete("/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Soft delete de um vídeo. O arquivo físico permanece até o TTL da Fase 7."""
    video = video_service.soft_delete(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vídeo não encontrado ou já removido",
        )
    return {"message": "Vídeo removido"}
