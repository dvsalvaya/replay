# Fase 4 — Buffer Circular + Salvar Momento
## Arquivo de Referência do Antigravity CLI

> **INSTRUÇÃO PARA O AGY:** Este arquivo é sua fonte de verdade durante toda a Fase 4.
> Consulte-o antes de iniciar cada minitarefa. Nunca pule uma task sem concluir a anterior.
> A Fase 3 deve estar 100% concluída antes de iniciar esta fase.
> Ao concluir cada task, marque o checkbox correspondente neste documento.

---

## 🗺️ Visão Geral da Fase

### Objetivo
Implementar o buffer circular de vídeo (últimos N segundos em memória) e o mecanismo de salvamento sob demanda: quando o usuário clicar "Salvar Momento", os últimos 120 segundos do buffer são processados pelo FFmpeg e salvos como MP4 em disco, com metadados registrados no SQLite.

### O Que Esta Fase Entrega
- Buffer circular thread-safe alimentado continuamente pela câmera
- Endpoint `POST /moments/save` que dispara o salvamento em background
- FFmpeg converte frames JPEG em memória → MP4 em disco
- Registro do vídeo salvo no SQLite com metadados
- Endpoint `GET /moments/jobs/{job_id}` para polling do status do job
- Botão "Salvar Momento" no frontend com feedback em tempo real

### O Que Esta Fase NÃO Entrega
- Interface de galeria (Fase 6)
- Corte de vídeo (Fase 6)
- TTL automático (Fase 7)
- Player de vídeo (Fase 6)

### Pré-requisitos
- Fase 3 concluída (câmera rodando, stream MJPEG funcionando)
- FFmpeg instalado no sistema operacional (não via pip)
- `app/videos/models.py` já existe com o model `Video` (criado no Prompt 01)

---

## 🏗️ Arquitetura da Fase 4

```
backend/
└── app/
    ├── domain/
    │   └── camera/
    │       ├── entities.py       ← MODIFICAR: adicionar VideoBuffer, SaveJob
    │       └── interfaces.py     ← MODIFICAR: adicionar IVideoWriter, IBufferRepository
    │
    ├── application/
    │   └── camera/
    │       └── use_cases.py      ← MODIFICAR: adicionar BufferUseCases, SaveMomentUseCase
    │
    ├── infrastructure/
    │   ├── camera/
    │   │   └── opencv_adapter.py ← MODIFICAR: alimentar buffer no _capture_loop
    │   └── video/
    │       ├── __init__.py
    │       └── ffmpeg_writer.py  ← NOVO: frames[] → MP4 via FFmpeg subprocess
    │
    ├── moments/                  ← NOVO (router de salvamento)
    │   ├── __init__.py
    │   ├── router.py             ← POST /moments/save, GET /moments/jobs/{job_id}
    │   ├── schemas.py            ← SaveMomentRequest, SaveMomentResponse, JobStatusResponse
    │   └── dependencies.py       ← get_save_moment_use_case, get_job_store
    │
    └── videos/
        └── models.py             ← JÁ EXISTE (Prompt 01) — apenas verificar colunas
```

### Regras de Dependência (NUNCA violar)
```
domain              → não importa nada do projeto
application         → importa apenas domain
infrastructure/video → importa domain + FFmpeg (subprocess)
infrastructure/camera → importa domain + OpenCV
moments/router      → importa application + schemas
```

---

## 📋 Estado de Progresso

> **AGY:** Atualize os checkboxes conforme completar cada task.

- [x] **Task 4.1** — Domain: VideoBuffer, SaveJob e novas interfaces
- [x] **Task 4.2** — Application: BufferUseCases e SaveMomentUseCase
- [x] **Task 4.3** — Infrastructure: Integrar buffer no OpenCVCameraAdapter
- [x] **Task 4.4** — Infrastructure: FFmpegWriter (frames → MP4)
- [x] **Task 4.5** — Interface: Rotas FastAPI do módulo /moments
- [x] **Task 4.6** — Frontend: Botão "Salvar Momento" + feedback

---

## 🔗 Contratos Entre Camadas

> **AGY:** Estes contratos são imutáveis. Todas as tasks devem respeitá-los.

### VideoBuffer
```python
@dataclass
class VideoBuffer:
    """
    Snapshot imutável do buffer no momento do salvamento.
    NÃO é o buffer em si — é uma cópia dos frames no momento do clique.
    """
    frames: list[Frame]          # cópia dos frames no momento do save
    captured_at: float           # unix timestamp do momento do snapshot
    duration_seconds: float      # duração real (pode ser < max se câmera recém iniciada)
    fps: float                   # FPS médio da captura
```

### SaveJob
```python
@dataclass
class SaveJob:
    """Representa um job de salvamento assíncrono."""
    job_id: str
    status: Literal["pending", "processing", "done", "error"]
    created_at: float
    completed_at: float | None
    video_id: int | None         # ID do Video no SQLite após salvar
    error_message: str | None
```

### IVideoWriter
```python
class IVideoWriter(ABC):
    @abstractmethod
    def write(
        self,
        frames: list[Frame],
        output_path: str,
        fps: float,
    ) -> tuple[str, float]:
        """
        Escreve frames como vídeo no output_path.
        Retorna: (caminho_absoluto, duracao_segundos)
        Lança: VideoWriteError se falhar.
        """
        ...
```

### Endpoints
```
POST /moments/save
  Auth: Bearer token obrigatório
  Body: { "title": "Gol incrível" }  ← title é opcional
  Response: { "job_id": "uuid", "status": "pending" }
  Comportamento: dispara BackgroundTask e retorna imediatamente

GET /moments/jobs/{job_id}
  Auth: Bearer token obrigatório
  Response: {
    "job_id": "...",
    "status": "pending|processing|done|error",
    "video_id": 42,        ← presente apenas quando status=done
    "error_message": null  ← presente apenas quando status=error
  }

GET /moments/
  Auth: Bearer token obrigatório
  Response: lista de Video (placeholder para Fase 6)
```

---

## ⚙️ Configurações Globais

> **AGY:** Adicionar ao `.env` e ao `app/config.py` antes de iniciar a Task 4.3.

```env
# Buffer
BUFFER_DURATION_SECONDS=120
BUFFER_MAX_FRAMES=1800

# Storage
VIDEOS_DIR=./storage/videos
TEMP_DIR=./storage/temp

# FFmpeg
FFMPEG_PATH=ffmpeg
FFMPEG_CRF=23
FFMPEG_PRESET=ultrafast
```

```python
# Em app/config.py — adicionar à classe Settings:
buffer_duration_seconds: int = 120
buffer_max_frames: int = 1800
videos_dir: str = "./storage/videos"
temp_dir: str = "./storage/temp"
ffmpeg_path: str = "ffmpeg"
ffmpeg_crf: int = 23
ffmpeg_preset: str = "ultrafast"
```

---

## 📦 Nova Dependência

Nenhuma dependência Python nova nesta fase. FFmpeg é um executável do sistema.

> **AGY:** Verificar se FFmpeg está instalado antes de iniciar a Task 4.4:
> ```bash
> ffmpeg -version
> ```
> Se não estiver instalado, instruir o desenvolvedor a instalar antes de continuar.
> - macOS: `brew install ffmpeg`
> - Ubuntu/Debian: `sudo apt install ffmpeg`
> - Windows: baixar em https://ffmpeg.org/download.html e adicionar ao PATH

---

---

# TASK 4.1 — Domain: VideoBuffer, SaveJob e Novas Interfaces

## Objetivo
Estender a camada de domínio com as entidades e interfaces necessárias para o buffer circular e o processo de salvamento. Nenhuma lógica de negócio aqui — apenas contratos e estruturas de dados.

## Arquivos a Modificar/Criar

```
app/domain/camera/
├── entities.py     ← MODIFICAR: adicionar VideoBuffer, SaveJob
└── interfaces.py   ← MODIFICAR: adicionar IVideoWriter, IJobStore
```

## Implementação

### Adicionar em `app/domain/camera/entities.py`

```python
# Adicionar imports no topo:
from typing import Literal

# Adicionar após as entidades existentes:

@dataclass
class VideoBuffer:
    """
    Snapshot imutável do conteúdo do buffer circular no momento do salvamento.
    Criado quando o usuário clica 'Salvar Momento'.
    """
    frames: list["Frame"]
    captured_at: float
    duration_seconds: float
    fps: float

    def __post_init__(self) -> None:
        if not self.frames:
            raise ValueError("VideoBuffer não pode ter lista de frames vazia")
        if self.fps <= 0:
            raise ValueError("FPS deve ser positivo")

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def estimated_size_bytes(self) -> int:
        return sum(len(f.data) for f in self.frames)


@dataclass
class SaveJob:
    """
    Representa um job assíncrono de salvamento de vídeo.
    Criado imediatamente ao receber o request de salvar.
    Atualizado quando o processamento termina (sucesso ou erro).
    """
    job_id: str
    status: Literal["pending", "processing", "done", "error"]
    created_at: float
    completed_at: float | None = None
    video_id: int | None = None
    error_message: str | None = None

    def mark_processing(self) -> None:
        self.status = "processing"

    def mark_done(self, video_id: int) -> None:
        import time
        self.status = "done"
        self.video_id = video_id
        self.completed_at = time.time()

    def mark_error(self, message: str) -> None:
        import time
        self.status = "error"
        self.error_message = message
        self.completed_at = time.time()

    @property
    def is_terminal(self) -> bool:
        return self.status in ("done", "error")
```

### Adicionar em `app/domain/camera/interfaces.py`

```python
# Adicionar imports no topo:
from typing import Optional

# Adicionar após ICameraAdapter:

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


class VideoWriteError(Exception):
    """Erro durante processamento ou escrita de vídeo."""
    pass
```

## Critérios de Aceitação da Task 4.1
- [ ] `from app.domain.camera.entities import VideoBuffer, SaveJob` funciona
- [ ] `from app.domain.camera.interfaces import IVideoWriter, IJobStore` funciona
- [ ] `VideoBuffer(frames=[], ...)` lança `ValueError`
- [ ] `SaveJob.mark_done(42)` muda status para "done" e seta video_id
- [ ] Nenhuma importação de OpenCV, FastAPI, SQLAlchemy ou FFmpeg no domain

---

---

# TASK 4.2 — Application: BufferUseCases e SaveMomentUseCase

## Objetivo
Criar os casos de uso que gerenciam o buffer e orquestram o salvamento. Esta camada coordena domain + infrastructure sem conhecer detalhes de implementação.

## Arquivos a Modificar

```
app/application/camera/
└── use_cases.py    ← MODIFICAR: adicionar BufferUseCases, SaveMomentUseCase
```

## Implementação

### Adicionar em `app/application/camera/use_cases.py`

```python
# Adicionar imports:
import os
import time
import uuid
from sqlalchemy.orm import Session
from app.domain.camera.entities import VideoBuffer, SaveJob
from app.domain.camera.interfaces import IVideoWriter, IJobStore, VideoWriteError
from app.videos.models import Video
from app.config import settings


class InMemoryJobStore(IJobStore):
    """
    Implementação em memória do IJobStore para o MVP.
    Jobs são perdidos se o servidor reiniciar — aceitável para MVP local.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, SaveJob] = {}

    def create(self, job: SaveJob) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> SaveJob | None:
        return self._jobs.get(job_id)

    def update(self, job: SaveJob) -> None:
        self._jobs[job.job_id] = job

    def list_all(self) -> list[SaveJob]:
        return list(self._jobs.values())


class SaveMomentUseCase:
    """
    Orquestra o salvamento de um momento:
    1. Pega snapshot do buffer
    2. Chama IVideoWriter para gerar o MP4
    3. Salva metadados no SQLite
    4. Atualiza o job com resultado
    """

    def __init__(
        self,
        writer: IVideoWriter,
        job_store: IJobStore,
    ) -> None:
        self._writer = writer
        self._job_store = job_store

    def create_job(self) -> SaveJob:
        """Cria e persiste um novo job com status pending."""
        job = SaveJob(
            job_id=str(uuid.uuid4()),
            status="pending",
            created_at=time.time(),
        )
        self._job_store.create(job)
        return job

    def execute(
        self,
        job_id: str,
        buffer: VideoBuffer,
        db: Session,
        title: str | None = None,
    ) -> None:
        """
        Executa o salvamento em background.
        Atualiza o job ao longo do processo.
        Deve ser chamado em BackgroundTask.
        """
        job = self._job_store.get(job_id)
        if not job:
            return

        job.mark_processing()
        self._job_store.update(job)

        try:
            # Garantir que o diretório de vídeos existe
            os.makedirs(settings.videos_dir, exist_ok=True)

            # Gerar nome único para o arquivo
            filename = f"moment_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(settings.videos_dir, filename)

            # Delegar a escrita do vídeo para a infraestrutura
            saved_path, duration = self._writer.write(
                frames=buffer.frames,
                output_path=output_path,
                fps=buffer.fps,
            )

            # Calcular tamanho do arquivo
            file_size = os.path.getsize(saved_path)

            # Calcular data de expiração
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(days=7)

            # Salvar metadados no banco
            video = Video(
                filename=filename,
                title=title,
                duration_seconds=duration,
                file_size_bytes=file_size,
                file_path=saved_path,
                expires_at=expires_at,
            )
            db.add(video)
            db.commit()
            db.refresh(video)

            job.mark_done(video_id=video.id)
            self._job_store.update(job)

        except (VideoWriteError, OSError, Exception) as e:
            job.mark_error(str(e))
            self._job_store.update(job)
            db.rollback()

    def get_job(self, job_id: str) -> SaveJob | None:
        return self._job_store.get(job_id)
```

## Critérios de Aceitação da Task 4.2
- [ ] `from app.application.camera.use_cases import SaveMomentUseCase, InMemoryJobStore` funciona
- [ ] `InMemoryJobStore` implementa todos os métodos de `IJobStore`
- [ ] `SaveMomentUseCase` não importa OpenCV nem FFmpeg diretamente
- [ ] `create_job()` retorna job com status "pending"
- [ ] Nenhuma referência a `cv2`, `subprocess` ou FFmpeg neste arquivo

---

---

# TASK 4.3 — Infrastructure: Integrar Buffer no OpenCVCameraAdapter

## Objetivo
Modificar o `OpenCVCameraAdapter` para alimentar um buffer circular `deque` a cada frame capturado. O buffer deve ser thread-safe e permitir snapshot atômico para o processo de salvamento.

## Arquivos a Modificar

```
app/infrastructure/camera/
└── opencv_adapter.py    ← MODIFICAR
```

## Implementação

### Modificações em `app/infrastructure/camera/opencv_adapter.py`

```python
# Adicionar imports no topo:
import collections
from app.domain.camera.entities import VideoBuffer
from app.config import settings

# Dentro da classe OpenCVCameraAdapter, adicionar no __init__:
self._buffer: collections.deque = collections.deque(
    maxlen=settings.buffer_max_frames
)
# _lock já existe da Fase 3 — o mesmo lock protege frame E buffer

# Dentro do _capture_loop, após criar o Frame e antes do with self._lock:
# (substituir o bloco "with self._lock" existente por:)
with self._lock:
    self._latest_frame = frame
    self._buffer.append(frame)

# Adicionar novo método público na classe:
def get_buffer_snapshot(self) -> VideoBuffer | None:
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

# Adicionar ao stop() — limpar buffer ao parar:
# Dentro de stop(), após self._latest_frame = None:
self._buffer.clear()
```

### Adicionar ao `ICameraAdapter` em `app/domain/camera/interfaces.py`

```python
# Adicionar método à interface ICameraAdapter:
@abstractmethod
def get_buffer_snapshot(self) -> Optional["VideoBuffer"]:
    """
    Retorna snapshot thread-safe do buffer circular atual.
    None se buffer vazio ou câmera parada.
    """
    ...
```

### Adicionar ao `CameraUseCases` em `app/application/camera/use_cases.py`

```python
# Adicionar método à classe CameraUseCases:
def get_buffer_snapshot(self) -> VideoBuffer | None:
    """Retorna snapshot do buffer para salvamento."""
    if not self._adapter.is_running():
        return None
    return self._adapter.get_buffer_snapshot()
```

## Critérios de Aceitação da Task 4.3
- [ ] `OpenCVCameraAdapter` tem atributo `_buffer` do tipo `collections.deque`
- [ ] `deque` tem `maxlen=settings.buffer_max_frames`
- [ ] `get_buffer_snapshot()` retorna `VideoBuffer` com frames copiados
- [ ] O mesmo `_lock` protege `_latest_frame` e `_buffer`
- [ ] `stop()` limpa o buffer
- [ ] Após 5 segundos de câmera rodando, `get_buffer_snapshot()` retorna frames com `duration_seconds > 0`

---

---

# TASK 4.4 — Infrastructure: FFmpegWriter (frames → MP4)

## Objetivo
Implementar `IVideoWriter` usando FFmpeg via subprocess. Recebe lista de frames JPEG em memória, grava temporariamente em disco, chama FFmpeg para encodar como MP4 e limpa os temporários.

## Pré-requisito
```bash
ffmpeg -version   # deve retornar versão sem erro
```

## Arquivos a Criar

```
app/infrastructure/video/
├── __init__.py
└── ffmpeg_writer.py    ← NOVO
```

## Implementação

### `app/infrastructure/video/ffmpeg_writer.py`

```python
import os
import subprocess
import tempfile
import shutil
import time
from app.domain.camera.entities import Frame
from app.domain.camera.interfaces import IVideoWriter, VideoWriteError
from app.config import settings


class FFmpegWriter(IVideoWriter):
    """
    Implementação de IVideoWriter usando FFmpeg via subprocess.

    Estratégia:
    1. Criar diretório temporário
    2. Salvar cada frame como arquivo JPEG numerado (frame_0001.jpg, ...)
    3. Chamar FFmpeg com input pattern para encodar MP4
    4. Limpar temporários independente de sucesso/falha
    """

    def write(
        self,
        frames: list[Frame],
        output_path: str,
        fps: float,
    ) -> tuple[str, float]:
        if not frames:
            raise VideoWriteError("Nenhum frame para processar")

        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Garantir que o diretório temp existe
        os.makedirs(settings.temp_dir, exist_ok=True)

        temp_dir = tempfile.mkdtemp(dir=settings.temp_dir)

        try:
            # 1. Salvar frames como JPEGs numerados
            self._write_frames_to_disk(frames, temp_dir)

            # 2. Montar e executar comando FFmpeg
            duration = self._run_ffmpeg(
                temp_dir=temp_dir,
                output_path=output_path,
                fps=fps,
                frame_count=len(frames),
            )

            return output_path, duration

        except subprocess.TimeoutExpired:
            raise VideoWriteError("FFmpeg excedeu o tempo limite de processamento")
        except subprocess.CalledProcessError as e:
            raise VideoWriteError(
                f"FFmpeg falhou com código {e.returncode}: {e.stderr}"
            )
        except OSError as e:
            raise VideoWriteError(f"Erro de disco ao salvar vídeo: {e}")
        finally:
            # Sempre limpar temporários, sucesso ou falha
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _write_frames_to_disk(self, frames: list[Frame], temp_dir: str) -> None:
        """Salva frames como JPEGs numerados no diretório temporário."""
        for i, frame in enumerate(frames):
            frame_path = os.path.join(temp_dir, f"frame_{i:06d}.jpg")
            with open(frame_path, "wb") as f:
                f.write(frame.data)

    def _run_ffmpeg(
        self,
        temp_dir: str,
        output_path: str,
        fps: float,
        frame_count: int,
    ) -> float:
        """
        Executa FFmpeg para encodar frames JPEG em MP4.
        Retorna a duração calculada em segundos.
        """
        input_pattern = os.path.join(temp_dir, "frame_%06d.jpg")

        cmd = [
            settings.ffmpeg_path,
            "-y",                          # sobrescrever sem perguntar
            "-framerate", str(fps),        # FPS de entrada
            "-i", input_pattern,           # padrão de entrada
            "-c:v", "libx264",             # codec H.264
            "-crf", str(settings.ffmpeg_crf),       # qualidade (23=default, menor=melhor)
            "-preset", settings.ffmpeg_preset,       # velocidade de encode (ultrafast no MVP)
            "-pix_fmt", "yuv420p",         # compatibilidade máxima (iOS, WhatsApp, etc)
            "-movflags", "+faststart",     # permite streaming progressivo
            output_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutos de timeout máximo
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        # Calcular duração estimada
        duration = frame_count / fps
        return duration
```

## Critérios de Aceitação da Task 4.4
- [ ] `from app.infrastructure.video.ffmpeg_writer import FFmpegWriter` funciona
- [ ] `FFmpegWriter` implementa `IVideoWriter`
- [ ] Diretório temporário é sempre limpo (mesmo em caso de erro)
- [ ] Lança `VideoWriteError` com mensagem clara em caso de falha
- [ ] `ffmpeg -version` retorna sem erro no ambiente de desenvolvimento
- [ ] Teste manual: criar 30 frames JPEG fictícios e chamar `.write()` gera um MP4 válido

---

---

# TASK 4.5 — Interface: Rotas FastAPI do Módulo /moments

## Objetivo
Criar o router `/moments` com os endpoints de salvamento e consulta de jobs. O endpoint de save dispara a operação em `BackgroundTasks` e retorna o `job_id` imediatamente.

## Arquivos a Criar/Modificar

```
app/moments/
├── __init__.py
├── router.py
├── schemas.py
└── dependencies.py

app/main.py    ← MODIFICAR: registrar router de moments
```

### `app/moments/schemas.py`

```python
from pydantic import BaseModel
from typing import Literal, Optional


class SaveMomentRequest(BaseModel):
    title: Optional[str] = None


class SaveMomentResponse(BaseModel):
    job_id: str
    status: Literal["pending"]
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "done", "error"]
    video_id: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[float] = None
```

### `app/moments/dependencies.py`

```python
from functools import lru_cache
from app.application.camera.use_cases import SaveMomentUseCase, InMemoryJobStore
from app.infrastructure.video.ffmpeg_writer import FFmpegWriter


@lru_cache(maxsize=1)
def get_job_store() -> InMemoryJobStore:
    return InMemoryJobStore()


@lru_cache(maxsize=1)
def get_save_moment_use_case() -> SaveMomentUseCase:
    return SaveMomentUseCase(
        writer=FFmpegWriter(),
        job_store=get_job_store(),
    )
```

### `app/moments/router.py`

```python
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
```

### Modificar `app/main.py`

```python
# Adicionar ao bloco de imports de routers:
from app.moments.router import router as moments_router

# Adicionar ao registro de routers:
app.include_router(moments_router)
```

## Critérios de Aceitação da Task 4.5
- [ ] `POST /moments/save` sem câmera retorna 409
- [ ] `POST /moments/save` com câmera rodando retorna `{ job_id, status: "pending" }`
- [ ] `GET /moments/jobs/{job_id}` retorna status atualizado
- [ ] Após polling até status "done", `video_id` está presente
- [ ] MP4 existe em `./storage/videos/` após job concluído
- [ ] `GET /moments/jobs/id-inexistente` retorna 404
- [ ] Todas as rotas retornam 401 sem token
- [ ] Swagger em `/docs` mostra as novas rotas

---

---

# TASK 4.6 — Frontend: Botão "Salvar Momento" + Feedback

## Objetivo
Adicionar ao Dashboard o botão "Salvar Momento" com feedback em tempo real usando polling do job. O usuário deve saber claramente se o salvamento está em andamento, se concluiu ou se falhou.

## Arquivos a Criar/Modificar

```
src/
├── services/
│   └── momentsService.ts     ← NOVO
├── hooks/
│   └── useSaveMoment.ts      ← NOVO
└── pages/
    └── DashboardPage.tsx     ← MODIFICAR
```

### `src/services/momentsService.ts`

```typescript
import { apiFetch } from '@/lib/api'

export interface SaveJobStatus {
  job_id: string
  status: 'pending' | 'processing' | 'done' | 'error'
  video_id: number | null
  error_message: string | null
  completed_at: number | null
}

export interface SaveMomentResponse {
  job_id: string
  status: 'pending'
  message: string
}

export const momentsService = {
  save: (title?: string) =>
    apiFetch<SaveMomentResponse>('/moments/save', {
      method: 'POST',
      body: JSON.stringify({ title: title ?? null }),
    }),

  getJobStatus: (jobId: string) =>
    apiFetch<SaveJobStatus>(`/moments/jobs/${jobId}`),
}
```

### `src/hooks/useSaveMoment.ts`

```typescript
import { useState, useRef, useCallback } from 'react'
import { momentsService, SaveJobStatus } from '@/services/momentsService'

type SaveState =
  | { phase: 'idle' }
  | { phase: 'saving'; jobId: string; message: string }
  | { phase: 'done'; videoId: number }
  | { phase: 'error'; message: string }

export function useSaveMoment() {
  const [state, setState] = useState<SaveState>({ phase: 'idle' })
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const pollJobStatus = useCallback(
    (jobId: string) => {
      pollRef.current = setInterval(async () => {
        try {
          const job: SaveJobStatus = await momentsService.getJobStatus(jobId)

          if (job.status === 'done' && job.video_id) {
            stopPolling()
            setState({ phase: 'done', videoId: job.video_id })
            // Voltar para idle após 3 segundos
            setTimeout(() => setState({ phase: 'idle' }), 3000)
          } else if (job.status === 'error') {
            stopPolling()
            setState({
              phase: 'error',
              message: job.error_message ?? 'Erro desconhecido',
            })
            setTimeout(() => setState({ phase: 'idle' }), 5000)
          }
          // 'pending' e 'processing' continuam o polling
        } catch {
          stopPolling()
          setState({ phase: 'error', message: 'Erro ao verificar status do salvamento' })
        }
      }, 1500) // polling a cada 1.5 segundos
    },
    [stopPolling]
  )

  const saveMoment = useCallback(
    async (title?: string) => {
      if (state.phase !== 'idle') return

      try {
        const response = await momentsService.save(title)
        setState({
          phase: 'saving',
          jobId: response.job_id,
          message: response.message,
        })
        pollJobStatus(response.job_id)
      } catch (err) {
        setState({
          phase: 'error',
          message: err instanceof Error ? err.message : 'Erro ao iniciar salvamento',
        })
        setTimeout(() => setState({ phase: 'idle' }), 5000)
      }
    },
    [state.phase, pollJobStatus]
  )

  return { state, saveMoment }
}
```

### Modificar `src/pages/DashboardPage.tsx`

Adicionar ao Dashboard existente:

```typescript
// Importar o novo hook:
import { useSaveMoment } from '@/hooks/useSaveMoment'

// Dentro do componente:
const { state: saveState, saveMoment } = useSaveMoment()

// Botão "Salvar Momento" — adicionar abaixo dos controles de câmera:
// Renderizar conforme o estado:
//
// phase === 'idle' && câmera rodando:
//   <Button onClick={() => saveMoment()}>⏺ Salvar Momento</Button>
//
// phase === 'idle' && câmera parada:
//   <Button disabled>⏺ Salvar Momento</Button>  (com tooltip: "Inicie a câmera primeiro")
//
// phase === 'saving':
//   <Button disabled>⏳ Salvando... ({saveState.message})</Button>
//
// phase === 'done':
//   <div className="text-green-600">✅ Momento salvo! (video #{saveState.videoId})</div>
//
// phase === 'error':
//   <div className="text-red-600">❌ {saveState.message}</div>
```

## Critérios de Aceitação da Task 4.6
- [ ] Botão "Salvar Momento" aparece no Dashboard
- [ ] Botão desabilitado quando câmera parada
- [ ] Clicar "Salvar Momento" com câmera rodando inicia o processo
- [ ] Estado "Salvando..." é exibido durante o processamento
- [ ] Mensagem de sucesso aparece após conclusão
- [ ] Mensagem de erro aparece em caso de falha
- [ ] Após 3s de sucesso ou 5s de erro, botão volta ao estado idle
- [ ] Polling para automaticamente após status terminal
- [ ] Sem erros no console do browser durante o fluxo completo

---

---

## 🧪 Critérios de Aceitação da Fase 4 Completa

Só considerar a Fase 4 concluída quando **todos** os itens abaixo forem verdadeiros:

### Fluxo Completo End-to-End
- [x] Iniciar câmera → aguardar 5s → clicar "Salvar Momento" → MP4 criado em `./storage/videos/`
- [x] `GET /moments/jobs/{job_id}` mostra progressão: pending → processing → done
- [x] Arquivo MP4 é reproduzível (testar com VLC ou similar)
- [x] Metadados corretos no SQLite: `filename`, `duration_seconds`, `file_size_bytes`, `expires_at`

### Resiliência
- [x] Clicar "Salvar" sem câmera iniciada retorna 409 com mensagem clara
- [x] Clicar "Salvar" com buffer vazio (câmera recém iniciada) retorna 422 com mensagem clara
- [x] Diretório temp é limpo após processamento (sucesso ou falha)
- [x] Job com FFmpeg ausente marca status "error" com mensagem legível

### Performance
- [x] Endpoint `POST /moments/save` retorna em menos de 200ms
- [x] Stream MJPEG não é interrompido durante o salvamento
- [x] Processamento de 120s de vídeo conclui em menos de 30s

### Arquitetura
- [x] `SaveMomentUseCase` não importa cv2, FFmpeg ou FastAPI diretamente
- [x] `FFmpegWriter` não importa FastAPI ou SQLAlchemy
- [x] `InMemoryJobStore` implementa `IJobStore` completamente
- [x] Diretórios `storage/videos/` e `storage/temp/` no `.gitignore`

---

## 🚨 Problemas Comuns e Soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| `ffmpeg: command not found` | FFmpeg não instalado | Instalar conforme OS e verificar PATH |
| MP4 não reproduz no browser | Falta `-pix_fmt yuv420p` | Garantir que o flag está no comando FFmpeg |
| Buffer sempre vazio | câmera parou silenciosamente | Verificar `GET /camera/status` e reiniciar |
| Job fica em "processing" | FFmpeg travou ou timeout | Verificar logs do servidor, reduzir buffer_max_frames |
| Disco cheio | Temp não foi limpo | Verificar `shutil.rmtree` no finally, checar `storage/temp/` |
| Alta latência no save | FFmpeg preset muito lento | Usar `ultrafast` em settings |
| `422 Buffer vazio` imediato | Buffer não alimentado | Aguardar pelo menos 2s após iniciar câmera |
| Session DB inválida em background | Session fechada antes do job terminar | Garantir que `db` é passado à BackgroundTask corretamente |

---

## 📝 Notas de Arquitetura para o Desenvolvedor

### Por que BackgroundTasks e não threading direto?
`BackgroundTasks` do FastAPI é gerenciado pelo framework: executa após a response ser enviada, dentro do mesmo processo, com acesso às dependências. Threading manual quebraria o gerenciamento de ciclo de vida do SQLAlchemy Session. Para o MVP local, BackgroundTasks é a solução certa.

### Por que InMemoryJobStore e não salvar no SQLite?
Jobs são efêmeros — duram minutos. Salvar no SQLite adiciona complexidade sem benefício real no MVP. Se o servidor reiniciar, os jobs pendentes já são inválidos de qualquer forma. Para produção futura: Redis com TTL automático.

### Por que copiar os frames antes de processar?
O buffer circular continua sendo alimentado pela thread de captura durante o processamento. Se usássemos uma referência direta ao deque, os frames mudariam enquanto o FFmpeg processa. Copiar garante que o snapshot é imutável e consistente.

### Por que `-preset ultrafast`?
Em uma máquina local com CPU modesta, encodar H.264 com qualidade alta pode levar minutos. `ultrafast` sacrifica um pouco de compressão por velocidade — o arquivo é maior, mas o usuário não espera 2 minutos para ver o resultado. Para produção: `medium` ou `slow`.

### Por que `-movflags +faststart`?
Este flag move os metadados do MP4 para o início do arquivo, permitindo que o browser comece a reproduzir antes do download completo. Sem isso, o player HTML5 esperaria o arquivo inteiro antes de iniciar — péssima UX mesmo em rede local.

