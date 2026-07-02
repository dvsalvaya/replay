# Fase 5 — Galeria de Vídeos + Player
## Arquivo de Referência do Antigravity CLI

> **INSTRUÇÃO PARA O AGY:** Este arquivo é sua fonte de verdade durante toda a Fase 5.
> Consulte-o antes de iniciar cada minitarefa. Nunca pule uma task sem concluir a anterior.
> As Fases 3 e 4 devem estar 100% concluídas antes de iniciar esta fase.
> Ao concluir cada task, marque o checkbox correspondente neste documento.

---

## 🗺️ Visão Geral da Fase

### Objetivo
Implementar a galeria de vídeos e o player modal. O usuário visualiza todos os momentos salvos em uma lista, clica para assistir em um modal, e pode deletar vídeos que não quer mais manter.

### O Que Esta Fase Entrega
- Endpoint `GET /videos` com lista paginada de vídeos não expirados
- Endpoint `DELETE /videos/{id}` com soft delete
- Endpoint `GET /videos/{id}/stream` para servir o arquivo MP4
- Página de Galeria no frontend (`/gallery`)
- Lista de vídeos com nome, data, duração e badge de expiração
- Modal com player HTML5 nativo
- Botão de deletar com confirmação
- Link de navegação no Dashboard para a Galeria

### O Que Esta Fase NÃO Entrega
- Corte de vídeo (descartado do escopo)
- Upload manual de vídeos
- Busca ou filtros na galeria
- Compartilhamento externo
- Thumbnails gerados automaticamente
- Paginação no frontend (apenas no backend)

### Pré-requisitos
- Fase 4 concluída (vídeos sendo salvos em `./storage/videos/` e registrados no SQLite)
- `app/videos/models.py` com model `Video` já existente
- Diretório `./storage/videos/` com ao menos um MP4 para testar

---

## 🏗️ Arquitetura da Fase 5

```
backend/
└── app/
    └── videos/
        ├── models.py       ← JÁ EXISTE — não modificar
        ├── schemas.py      ← MODIFICAR: adicionar VideoResponse, VideoListResponse
        ├── router.py       ← MODIFICAR: implementar GET /videos, GET /videos/{id}/stream, DELETE /videos/{id}
        └── service.py      ← NOVO: lógica de negócio separada do router

frontend/
└── src/
    ├── services/
    │   └── videoService.ts       ← NOVO
    ├── hooks/
    │   └── useVideos.ts          ← NOVO
    ├── components/
    │   └── gallery/
    │       ├── VideoList.tsx     ← NOVO
    │       ├── VideoCard.tsx     ← NOVO
    │       └── VideoModal.tsx    ← NOVO
    └── pages/
        ├── GalleryPage.tsx       ← NOVO
        └── DashboardPage.tsx     ← MODIFICAR: adicionar link para galeria
```

### Regras de Dependência (NUNCA violar)
```
videos/service.py  → importa models + config (nunca importa router)
videos/router.py   → importa service + schemas + security
GalleryPage        → usa useVideos hook
useVideos          → usa videoService
videoService       → usa apiFetch de lib/api.ts
```

---

## 📋 Estado de Progresso

> **AGY:** Atualize os checkboxes conforme completar cada task.

- [x] **Task 5.1** — Backend: Schemas e Service de Vídeos
- [x] **Task 5.2** — Backend: Rotas GET /videos, GET /videos/{id}/stream e DELETE /videos/{id}
- [x] **Task 5.3** — Frontend: videoService + useVideos hook
- [x] **Task 5.4** — Frontend: Componentes VideoList, VideoCard e VideoModal
- [x] **Task 5.5** — Frontend: GalleryPage + rota + link no Dashboard

---

## 🔗 Contratos Entre Camadas

> **AGY:** Estes contratos são imutáveis. Todas as tasks devem respeitá-los.

### VideoResponse (schema de saída)
```python
class VideoResponse(BaseModel):
    id: int
    filename: str
    title: str | None
    duration_seconds: float
    file_size_bytes: int
    created_at: datetime
    expires_at: datetime
    days_until_expiry: int       # calculado: (expires_at - now).days
    is_expiring_soon: bool       # True se days_until_expiry <= 2

    model_config = ConfigDict(from_attributes=True)
```

### VideoListResponse (paginação simples)
```python
class VideoListResponse(BaseModel):
    items: list[VideoResponse]
    total: int
    page: int
    page_size: int
```

### Endpoints
```
GET /videos?page=1&page_size=20
  Auth: Bearer token obrigatório
  Response: VideoListResponse
  Filtro: apenas vídeos onde is_deleted=False e expires_at > now()
  Ordem: created_at DESC (mais recente primeiro)

GET /videos/{id}/stream
  Auth: Bearer token via query param ?token=<jwt>
  Response: FileResponse (MP4) com headers corretos
  404 se vídeo não existe, deletado ou expirado

DELETE /videos/{id}
  Auth: Bearer token obrigatório
  Response: { "message": "Vídeo removido" }
  Comportamento: soft delete (is_deleted=True), não apaga o arquivo fisicamente
  404 se vídeo não existe ou já deletado
```

### Tipo TypeScript (frontend)
```typescript
interface Video {
  id: number
  filename: string
  title: string | null
  duration_seconds: number
  file_size_bytes: number
  created_at: string          // ISO 8601
  expires_at: string          // ISO 8601
  days_until_expiry: number
  is_expiring_soon: boolean
}

interface VideoListResponse {
  items: Video[]
  total: number
  page: number
  page_size: number
}
```

---

## ⚙️ Sem Novas Configurações

Esta fase não adiciona variáveis de ambiente. Usa `VIDEOS_DIR` já definido na Fase 4.

---

---

# TASK 5.1 — Backend: Schemas e Service de Vídeos

## Objetivo
Criar os schemas Pydantic de resposta e o service com a lógica de negócio de listagem e deleção. Separar lógica do router desde o início evita que o router vire um "god function".

## Arquivos a Criar/Modificar

```
app/videos/
├── schemas.py    ← MODIFICAR
└── service.py    ← NOVO
```

## Implementação

### `app/videos/schemas.py` (substituir conteúdo atual)

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional


class VideoResponse(BaseModel):
    id: int
    filename: str
    title: Optional[str]
    duration_seconds: float
    file_size_bytes: int
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def days_until_expiry(self) -> int:
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    @computed_field
    @property
    def is_expiring_soon(self) -> bool:
        return self.days_until_expiry <= 2


class VideoListResponse(BaseModel):
    items: list[VideoResponse]
    total: int
    page: int
    page_size: int
```

### `app/videos/service.py` (criar do zero)

```python
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
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
```

## Critérios de Aceitação da Task 5.1
- [ ] `from app.videos.schemas import VideoResponse, VideoListResponse` funciona
- [ ] `from app.videos.service import video_service` funciona
- [ ] `VideoResponse` tem `computed_field` para `days_until_expiry` e `is_expiring_soon`
- [ ] `VideoService` não importa FastAPI, routers ou schemas
- [ ] `soft_delete` não deleta o arquivo físico do disco
- [ ] `list_active` filtra corretamente `is_deleted=False` e `expires_at > now()`

---

---

# TASK 5.2 — Backend: Rotas de Vídeo

## Objetivo
Implementar os três endpoints de vídeo usando o `VideoService`. O endpoint de stream usa `FileResponse` do FastAPI para servir o MP4 com os headers corretos para o player HTML5.

## Arquivos a Modificar

```
app/videos/
└── router.py    ← MODIFICAR (substituir placeholder da Fase 1)
```

## Implementação

### `app/videos/router.py`

```python
import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
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
    username = verify_token(token)
    if not username:
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
```

### Verificar `app/core/security.py`

O endpoint de stream chama `verify_token(token)` diretamente. Confirmar que esta função já existe e exporta o username, ou criá-la:

```python
# Adicionar em app/core/security.py se não existir:
def verify_token(token: str) -> str | None:
    """
    Valida um JWT e retorna o username ou None se inválido.
    Usado diretamente (não como Depends) em rotas que recebem token via query param.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        return username if username else None
    except JWTError:
        return None
```

## Critérios de Aceitação da Task 5.2
- [ ] `GET /videos` retorna `VideoListResponse` com lista vazia se não há vídeos
- [ ] `GET /videos` retorna vídeos ordenados por `created_at DESC`
- [ ] `GET /videos/{id}/stream?token=<jwt>` retorna o arquivo MP4
- [ ] `GET /videos/{id}/stream?token=<jwt>` retorna 404 para vídeo inexistente
- [ ] `GET /videos/{id}/stream` sem token retorna 401
- [ ] `DELETE /videos/{id}` marca `is_deleted=True` no banco
- [ ] `DELETE /videos/{id}` NÃO apaga o arquivo do disco
- [ ] `DELETE /videos/{id}` retorna 404 para vídeo já deletado
- [ ] Todas as rotas (exceto stream) retornam 401 sem Bearer token
- [ ] Swagger em `/docs` mostra as 3 rotas

---

---

# TASK 5.3 — Frontend: videoService e useVideos Hook

## Objetivo
Criar a camada de serviço e o hook de dados para a galeria. Seguindo o mesmo padrão dos serviços anteriores: `videoService` chama a API, `useVideos` gerencia estado e loading.

## Arquivos a Criar

```
src/
├── services/
│   └── videoService.ts    ← NOVO
└── hooks/
    └── useVideos.ts       ← NOVO
```

## Implementação

### `src/services/videoService.ts`

```typescript
import { apiFetch, getAuthToken } from '@/lib/api'

export interface Video {
  id: number
  filename: string
  title: string | null
  duration_seconds: number
  file_size_bytes: number
  created_at: string
  expires_at: string
  days_until_expiry: number
  is_expiring_soon: boolean
}

export interface VideoListResponse {
  items: Video[]
  total: number
  page: number
  page_size: number
}

export const videoService = {
  list: (page = 1, pageSize = 20) =>
    apiFetch<VideoListResponse>(`/videos?page=${page}&page_size=${pageSize}`),

  delete: (id: number) =>
    apiFetch<{ message: string }>(`/videos/${id}`, { method: 'DELETE' }),

  getStreamUrl: (id: number): string => {
    const token = getAuthToken()
    return `${import.meta.env.VITE_API_URL}/videos/${id}/stream?token=${token}`
  },
}
```

> **NOTA PARA O AGY:** `getAuthToken()` deve ser exportado de `src/lib/api.ts`.
> Se ainda não existe, adicionar:
> ```typescript
> export function getAuthToken(): string | null {
>   return authToken  // variável de módulo existente
> }
> ```

### `src/hooks/useVideos.ts`

```typescript
import { useState, useEffect, useCallback } from 'react'
import { videoService, Video, VideoListResponse } from '@/services/videoService'

interface UseVideosReturn {
  videos: Video[]
  total: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  deleteVideo: (id: number) => Promise<void>
  isDeleting: boolean
}

export function useVideos(): UseVideosReturn {
  const [data, setData] = useState<VideoListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchVideos = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await videoService.list()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar vídeos')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchVideos()
  }, [fetchVideos])

  const deleteVideo = useCallback(async (id: number) => {
    try {
      setIsDeleting(true)
      await videoService.delete(id)
      // Atualiza a lista localmente sem refetch
      setData(prev =>
        prev
          ? {
              ...prev,
              items: prev.items.filter(v => v.id !== id),
              total: prev.total - 1,
            }
          : null
      )
    } catch (err) {
      throw err  // deixa o componente tratar o erro
    } finally {
      setIsDeleting(false)
    }
  }, [])

  return {
    videos: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    error,
    refetch: fetchVideos,
    deleteVideo,
    isDeleting,
  }
}
```

## Critérios de Aceitação da Task 5.3
- [ ] `videoService.list()` chama `GET /videos` e retorna `VideoListResponse`
- [ ] `videoService.delete(id)` chama `DELETE /videos/{id}`
- [ ] `videoService.getStreamUrl(id)` retorna URL com token no query param
- [ ] `getAuthToken()` exportado de `src/lib/api.ts`
- [ ] `useVideos()` retorna `isLoading=true` no primeiro render
- [ ] `deleteVideo()` atualiza lista localmente sem refetch desnecessário
- [ ] Nenhum `any` explícito nos tipos

---

---

# TASK 5.4 — Frontend: Componentes da Galeria

## Objetivo
Criar os três componentes da galeria: `VideoCard` (item da lista), `VideoList` (lista completa) e `VideoModal` (player em modal). Componentes pequenos, focados e reutilizáveis.

## Arquivos a Criar

```
src/components/gallery/
├── VideoCard.tsx     ← NOVO
├── VideoList.tsx     ← NOVO
└── VideoModal.tsx    ← NOVO
```

## Implementação

### `src/components/gallery/VideoCard.tsx`

```typescript
import { Video } from '@/services/videoService'
import { Button } from '@/components/ui/button'

interface VideoCardProps {
  video: Video
  onPlay: (video: Video) => void
  onDelete: (id: number) => void
  isDeleting: boolean
}

// Utilitários locais
function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatFileSize(bytes: number): string {
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function VideoCard({ video, onPlay, onDelete, isDeleting }: VideoCardProps) {
  const title = video.title ?? video.filename

  return (
    <div className="flex items-center justify-between py-3 px-4 border-b border-border last:border-0">
      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{title}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {formatDate(video.created_at)} · {formatDuration(video.duration_seconds)} · {formatFileSize(video.file_size_bytes)}
        </p>
        {/* Badge de expiração */}
        {video.is_expiring_soon && (
          <span className="inline-block mt-1 text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
            Expira em {video.days_until_expiry}d
          </span>
        )}
        {!video.is_expiring_soon && (
          <span className="inline-block mt-1 text-xs text-muted-foreground">
            Expira em {video.days_until_expiry}d
          </span>
        )}
      </div>

      {/* Ações */}
      <div className="flex items-center gap-2 ml-4 flex-shrink-0">
        <Button
          size="sm"
          variant="default"
          onClick={() => onPlay(video)}
        >
          ▶ Play
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={() => onDelete(video.id)}
          disabled={isDeleting}
        >
          Deletar
        </Button>
      </div>
    </div>
  )
}
```

### `src/components/gallery/VideoList.tsx`

```typescript
import { Video } from '@/services/videoService'
import { VideoCard } from './VideoCard'

interface VideoListProps {
  videos: Video[]
  onPlay: (video: Video) => void
  onDelete: (id: number) => void
  isDeleting: boolean
}

export function VideoList({ videos, onPlay, onDelete, isDeleting }: VideoListProps) {
  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <p className="text-lg">Nenhum momento salvo ainda.</p>
        <p className="text-sm mt-1">Inicie a câmera e clique em "Salvar Momento" para começar.</p>
      </div>
    )
  }

  return (
    <div className="divide-y divide-border rounded-lg border border-border bg-card">
      {videos.map(video => (
        <VideoCard
          key={video.id}
          video={video}
          onPlay={onPlay}
          onDelete={onDelete}
          isDeleting={isDeleting}
        />
      ))}
    </div>
  )
}
```

### `src/components/gallery/VideoModal.tsx`

```typescript
import { useEffect, useRef } from 'react'
import { Video } from '@/services/videoService'
import { videoService } from '@/services/videoService'
import { Button } from '@/components/ui/button'

interface VideoModalProps {
  video: Video | null
  onClose: () => void
}

export function VideoModal({ video, onClose }: VideoModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  // Pausa e reseta o vídeo ao fechar
  useEffect(() => {
    if (!video && videoRef.current) {
      videoRef.current.pause()
      videoRef.current.src = ''
    }
  }, [video])

  // Fechar com Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  if (!video) return null

  const streamUrl = videoService.getStreamUrl(video.id)
  const title = video.title ?? video.filename

  return (
    // Overlay — clique fora fecha
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
      onClick={onClose}
    >
      {/* Modal — clique dentro não propaga */}
      <div
        className="relative w-full max-w-3xl mx-4 bg-background rounded-xl shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-sm font-medium truncate">{title}</h2>
          <Button size="sm" variant="ghost" onClick={onClose}>
            ✕ Fechar
          </Button>
        </div>

        {/* Player */}
        <div className="bg-black aspect-video">
          <video
            ref={videoRef}
            src={streamUrl}
            controls
            autoPlay
            className="w-full h-full"
          >
            Seu browser não suporta reprodução de vídeo.
          </video>
        </div>

        {/* Footer com metadados */}
        <div className="px-4 py-2 text-xs text-muted-foreground flex gap-4">
          <span>
            {new Date(video.created_at).toLocaleString('pt-BR')}
          </span>
          <span>
            {Math.floor(video.duration_seconds / 60)}:{String(Math.floor(video.duration_seconds % 60)).padStart(2, '0')}
          </span>
          <span>
            {(video.file_size_bytes / (1024 * 1024)).toFixed(1)} MB
          </span>
        </div>
      </div>
    </div>
  )
}
```

## Critérios de Aceitação da Task 5.4
- [ ] `VideoCard` exibe nome, data, duração, tamanho e badge de expiração
- [ ] Badge âmbar aparece apenas quando `is_expiring_soon=true`
- [ ] Botão "Play" chama `onPlay` com o vídeo correto
- [ ] Botão "Deletar" chama `onDelete` com o id correto
- [ ] `VideoList` exibe estado vazio quando `videos.length === 0`
- [ ] `VideoModal` abre com `autoPlay` ao receber um vídeo
- [ ] `VideoModal` fecha ao clicar no overlay
- [ ] `VideoModal` fecha ao pressionar Escape
- [ ] Clicar dentro do modal não o fecha
- [ ] Player pausa e limpa `src` ao fechar o modal (evita vídeo rodando em background)

---

---

# TASK 5.5 — Frontend: GalleryPage + Rota + Link no Dashboard

## Objetivo
Criar a página da galeria, registrá-la como rota protegida e adicionar o link de navegação no Dashboard existente.

## Arquivos a Criar/Modificar

```
src/
├── pages/
│   ├── GalleryPage.tsx        ← NOVO
│   └── DashboardPage.tsx      ← MODIFICAR
└── App.tsx                    ← MODIFICAR: adicionar rota /gallery
```

### `src/pages/GalleryPage.tsx`

```typescript
import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useVideos } from '@/hooks/useVideos'
import { VideoList } from '@/components/gallery/VideoList'
import { VideoModal } from '@/components/gallery/VideoModal'
import { Video } from '@/services/videoService'
import { Button } from '@/components/ui/button'

export function GalleryPage() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const { videos, total, isLoading, error, deleteVideo, isDeleting } = useVideos()
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const handlePlay = useCallback((video: Video) => {
    setSelectedVideo(video)
  }, [])

  const handleCloseModal = useCallback(() => {
    setSelectedVideo(null)
  }, [])

  const handleDelete = useCallback(async (id: number) => {
    // Fechar modal se o vídeo deletado estava sendo reproduzido
    if (selectedVideo?.id === id) {
      setSelectedVideo(null)
    }
    try {
      setDeleteError(null)
      await deleteVideo(id)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Erro ao deletar vídeo')
    }
  }, [deleteVideo, selectedVideo])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-medium">Sports Highlights</h1>
          <nav className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
              Câmera
            </Button>
            <Button variant="secondary" size="sm">
              Galeria
            </Button>
          </nav>
        </div>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          Sair
        </Button>
      </header>

      {/* Conteúdo */}
      <main className="max-w-3xl mx-auto px-6 py-8">
        {/* Título + contador */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-medium">Momentos Salvos</h2>
          {!isLoading && (
            <span className="text-sm text-muted-foreground">
              {total} {total === 1 ? 'vídeo' : 'vídeos'}
            </span>
          )}
        </div>

        {/* Estados */}
        {isLoading && (
          <div className="flex justify-center py-16">
            <p className="text-muted-foreground">Carregando...</p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {deleteError && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive mb-4">
            {deleteError}
          </div>
        )}

        {!isLoading && !error && (
          <VideoList
            videos={videos}
            onPlay={handlePlay}
            onDelete={handleDelete}
            isDeleting={isDeleting}
          />
        )}
      </main>

      {/* Modal */}
      <VideoModal video={selectedVideo} onClose={handleCloseModal} />
    </div>
  )
}
```

### Modificar `src/App.tsx` — adicionar rota `/gallery`

```typescript
// Adicionar import:
import { GalleryPage } from '@/pages/GalleryPage'

// Adicionar rota protegida:
// Dentro do bloco de rotas protegidas (ProtectedRoute):
{ path: '/gallery', element: <GalleryPage /> }
```

### Modificar `src/pages/DashboardPage.tsx` — adicionar link para galeria

```typescript
// Adicionar import:
import { useNavigate } from 'react-router-dom'

// No header do Dashboard, adicionar nav com link para galeria:
// Seguindo o mesmo padrão de navegação do GalleryPage:
<nav className="flex gap-2">
  <Button variant="secondary" size="sm">
    Câmera
  </Button>
  <Button variant="ghost" size="sm" onClick={() => navigate('/gallery')}>
    Galeria
  </Button>
</nav>
```

### Adicionar rota em `src/lib/routes.ts`

```typescript
// Adicionar à lista de rotas:
export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  GALLERY: '/gallery',    // ← adicionar
} as const
```

## Critérios de Aceitação da Task 5.5
- [ ] `/gallery` está registrada como rota protegida no `App.tsx`
- [ ] Acessar `/gallery` sem login redireciona para `/login`
- [ ] `GalleryPage` exibe lista de vídeos após carregar
- [ ] Contador de vídeos aparece no header
- [ ] Clicar "Play" abre o modal com o vídeo correto
- [ ] Deletar um vídeo remove-o da lista imediatamente
- [ ] Se vídeo sendo reproduzido for deletado, modal fecha
- [ ] Dashboard tem link de navegação para `/gallery`
- [ ] Galeria tem link de navegação para `/dashboard`
- [ ] `npm run build` passa sem erros TypeScript

---

---

## 🧪 Critérios de Aceitação da Fase 5 Completa

Só considerar a Fase 5 concluída quando **todos** os itens abaixo forem verdadeiros:

### Fluxo End-to-End
- [x] Salvar momento (Fase 4) → ir para galeria → vídeo aparece na lista
- [x] Clicar Play → modal abre → vídeo reproduz automaticamente
- [x] Fechar modal → vídeo para de tocar
- [x] Clicar Deletar → vídeo some da lista instantaneamente
- [x] Vídeo deletado não reaparece após `refetch`

### Backend
- [x] `GET /videos` retorna lista ordenada por data decrescente
- [x] `GET /videos/{id}/stream?token=<jwt>` serve o MP4 com `Accept-Ranges: bytes`
- [x] `DELETE /videos/{id}` retorna 200 e seta `is_deleted=True` no banco
- [x] `DELETE /videos/{id}` não apaga arquivo do disco
- [x] Vídeo com `is_deleted=True` não aparece em `GET /videos`
- [x] Vídeo com `expires_at` no passado não aparece em `GET /videos`

### Frontend
- [x] Estado de loading exibido enquanto busca vídeos
- [x] Estado vazio exibido quando não há vídeos
- [x] Erro de API exibido com mensagem clara
- [x] Modal fecha com Escape e com clique no overlay
- [x] Navegação entre Dashboard e Galeria funciona em ambas direções
- [x] `npm run build` passa sem erros TypeScript

### Qualidade
- [x] Nenhum `console.error` ou `console.warn` no browser durante uso normal
- [x] `VideoService` não importa nada do React
- [x] `useVideos` não contém lógica de UI
- [x] Componentes de galeria não fazem fetch diretamente

---

## 🚨 Problemas Comuns e Soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| Player não reproduz o vídeo | Token inválido no stream URL | Verificar se `getAuthToken()` retorna o token correto |
| Vídeo reproduz sem áudio | MP4 gerado sem stream de áudio | Normal — webcam captura apenas vídeo no MVP |
| Modal não fecha com Escape | Event listener não registrado | Verificar `useEffect` no `VideoModal` |
| Vídeo some da lista mas volta ao refetch | `deleteVideo` no backend falhou silenciosamente | Checar retorno do `DELETE` e tratar erro corretamente |
| `Accept-Ranges` ausente | FileResponse sem headers | Garantir que o header está no `FileResponse` do backend |
| Player trava ao trocar vídeos | `src` do `<video>` não foi limpo | Garantir `videoRef.current.src = ''` no `useEffect` de fechamento |
| Galeria carrega infinitamente | Token expirado | Fazer logout e login novamente |

---

## 📝 Notas de Arquitetura para o Desenvolvedor

### Por que soft delete e não delete físico?
Deletar o arquivo físico imediatamente cria dois riscos: (1) o arquivo pode estar sendo reproduzido no player no momento do delete, (2) não há como desfazer. Com soft delete, o arquivo fica em disco até o TTL da Fase 7 fazer a limpeza real. O usuário tem a sensação de que deletou, mas o sistema tem uma janela de segurança.

### Por que `Accept-Ranges: bytes` no stream?
Sem esse header, o player HTML5 não consegue fazer seeking (arrastar a barra de progresso). O browser precisa do suporte a range requests para pular para qualquer ponto do vídeo sem baixar tudo. É um header de 2 palavras que muda completamente a experiência de reprodução.

### Por que o `deleteVideo` atualiza localmente e não faz refetch?
Fazer refetch após cada delete causa um flash visual (loading → lista) que é desnecessário. Atualizar o estado local é instantâneo e é correto porque o backend confirmou o delete. Se houvesse múltiplos usuários, o refetch seria necessário. Para um MVP com 1 usuário, update local é a decisão certa.

### Por que `aspect-video` no container do player?
`aspect-video` é uma classe Tailwind que força proporção 16:9. Sem ela, o player colapsa para altura 0 enquanto o vídeo carrega, causando um salto de layout. Com ela, o espaço é reservado imediatamente, e o vídeo preenche suavemente ao carregar.

### Por que o modal fecha ao deletar o vídeo reproduzido?
Se o modal continuasse aberto após o delete, o player tentaria continuar fazendo requests para um endpoint que retornaria 404. Fechar o modal antecipadamente é mais limpo e evita erros no console.

