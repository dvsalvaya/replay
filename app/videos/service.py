from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.videos.models import Video


class VideoService:
    """
    Lógica de negócio para operações com vídeos.
    Não conhece FastAPI — apenas SQLAlchemy e models.
    """

    def list_active(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Video], int]:
        """
        Lista vídeos ativos (não deletados e não expirados).
        Retorna tupla (items, total) para paginação.
        """
        query = (
            db.query(Video)
            .filter(
                Video.is_deleted == False,
                Video.expires_at > datetime.utcnow(),
            )
            .order_by(desc(Video.created_at))
        )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    def get_active_by_id(self, db: Session, video_id: int) -> Video | None:
        """
        Retorna vídeo ativo por ID ou None se não encontrado/deletado/expirado.
        """
        return (
            db.query(Video)
            .filter(
                Video.id == video_id,
                Video.is_deleted == False,
                Video.expires_at > datetime.utcnow(),
            )
            .first()
        )

    def soft_delete(self, db: Session, video_id: int) -> Video | None:
        """
        Marca vídeo como deletado (soft delete).
        Retorna o vídeo atualizado ou None se não encontrado.
        NÃO apaga o arquivo físico — isso fica para o TTL da Fase 7.
        """
        video = self.get_active_by_id(db, video_id)
        if not video:
            return None

        video.is_deleted = True
        db.commit()
        db.refresh(video)
        return video


video_service = VideoService()
