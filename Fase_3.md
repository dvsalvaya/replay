# Fase 3 — Captura de Vídeo ao Vivo + Stream MJPEG
## Arquivo de Referência do Antigravity CLI

> **INSTRUÇÃO PARA O AGY:** Este arquivo é sua fonte de verdade durante toda a Fase 3.
> Consulte-o antes de iniciar cada minitarefa. Nunca pule uma task sem concluir a anterior.
> Ao concluir cada task, marque o checkbox correspondente neste documento.

---

## 🗺️ Visão Geral da Fase

### Objetivo
Implementar a camada de captura de vídeo ao vivo no backend, expor um stream MJPEG via FastAPI e exibir o preview em tempo real no frontend — tudo seguindo os princípios de Arquitetura Limpa.

### O Que Esta Fase Entrega
- Câmera (webcam) sendo capturada continuamente pelo backend
- Preview ao vivo acessível via `http://localhost:8000/camera/stream`
- Frontend exibindo o preview em tempo real no Dashboard
- Fundação para o buffer circular (Fase 4)

### O Que Esta Fase NÃO Entrega
- Buffer circular (Fase 4)
- Salvar vídeo (Fase 4)
- Processamento FFmpeg (Fase 5)
- Corte de vídeo (Fase 6)

---

## 🏗️ Arquitetura da Fase 3

```
backend/
└── app/
    ├── domain/                      ← NOVO (camada mais interna)
    │   └── camera/
    │       ├── __init__.py
    │       ├── entities.py          ← CaptureSession, Frame, CameraStatus
    │       └── interfaces.py        ← ICameraAdapter (ABC pura)
    │
    ├── application/                 ← NOVO
    │   └── camera/
    │       ├── __init__.py
    │       └── use_cases.py         ← StartCapture, StopCapture, GetFrame
    │
    ├── infrastructure/              ← NOVO
    │   └── camera/
    │       ├── __init__.py
    │       └── opencv_adapter.py    ← Implementação concreta com OpenCV
    │
    ├── camera/                      ← NOVO (interface layer — rotas FastAPI)
    │   ├── __init__.py
    │   ├── router.py                ← GET /camera/stream, GET /camera/status
    │   ├── schemas.py               ← CameraStatusResponse
    │   └── dependencies.py          ← get_camera_use_case (DI)
    │
    └── main.py                      ← MODIFICADO (registrar router de câmera)
```

### Regras de Dependência (NUNCA violar)
```
domain        → não importa nada do projeto
application   → importa apenas domain
infrastructure → importa domain + libs externas (OpenCV)
camera/router → importa application + schemas
main.py       → importa routers
```

---

## 📋 Estado de Progresso

> **AGY:** Atualize os checkboxes conforme completar cada task.

- [x] **Task 3.1** — Domain: Entidades e Interface
- [x] **Task 3.2** — Application: Use Cases
- [x] **Task 3.3** — Infrastructure: Adaptador OpenCV
- [x] **Task 3.4** — Interface: Rotas FastAPI + Stream MJPEG
- [x] **Task 3.5** — Frontend: Preview ao Vivo no Dashboard

---

## 🔗 Contratos Entre Camadas

> **AGY:** Estes contratos são imutáveis. Todas as tasks devem respeitá-los.

### Frame
```python
@dataclass
class Frame:
    data: bytes          # JPEG encoded
    width: int
    height: int
    timestamp: float     # unix timestamp
```

### CameraStatus
```python
@dataclass
class CameraStatus:
    is_running: bool
    device_index: int
    fps: float
    resolution: tuple[int, int]   # (width, height)
    error: str | None
```

### ICameraAdapter (interface)
```python
class ICameraAdapter(ABC):
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def get_frame(self) -> Frame | None: ...

    @abstractmethod
    def get_status(self) -> CameraStatus: ...

    @abstractmethod
    def is_running(self) -> bool: ...
```

### Endpoint de Stream
```
GET /camera/stream
  Content-Type: multipart/x-mixed-replace; boundary=frame
  Auth: Bearer token obrigatório
  Response: stream infinito de frames MJPEG

GET /camera/status
  Auth: Bearer token obrigatório
  Response: CameraStatusResponse (JSON)

POST /camera/start
  Auth: Bearer token obrigatório
  Response: { "message": "Câmera iniciada" }

POST /camera/stop
  Auth: Bearer token obrigatório
  Response: { "message": "Câmera parada" }
```

---

## ⚙️ Configurações Globais

> **AGY:** Adicionar ao `.env` e ao `app/config.py` antes de iniciar a Task 3.3.

```env
# Camera
CAMERA_DEVICE_INDEX=0
CAMERA_FPS=15
CAMERA_WIDTH=1280
CAMERA_HEIGHT=720
CAMERA_JPEG_QUALITY=70
```

```python
# Em app/config.py — adicionar à classe Settings:
camera_device_index: int = 0
camera_fps: int = 15
camera_width: int = 1280
camera_height: int = 720
camera_jpeg_quality: int = 70
```

---

## 📦 Nova Dependência

> **AGY:** Adicionar ao `pyproject.toml` e rodar `uv sync` antes da Task 3.3.

```toml
dependencies = [
    # ... existentes ...
    "opencv-python-headless>=4.9.0",
]
```

> Usar `opencv-python-headless` (sem GUI), pois não precisamos de janelas nativas do OpenCV.

---

---

# TASK 3.1 — Domain: Entidades e Interface

## Objetivo
Criar a camada de domínio da câmera: entidades puras e a interface (contrato) que qualquer adaptador de câmera deve implementar. Esta camada não conhece OpenCV, FastAPI ou qualquer lib externa.

## Arquivos a Criar

```
app/domain/
├── __init__.py
└── camera/
    ├── __init__.py
    ├── entities.py
    └── interfaces.py
```

## Implementação

### `app/domain/__init__.py`
```python
# vazio
```

### `app/domain/camera/__init__.py`
```python
# vazio
```

### `app/domain/camera/entities.py`
```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Frame:
    """Representa um frame capturado da câmera, já encodado em JPEG."""
    data: bytes
    width: int
    height: int
    timestamp: float

    def __post_init__(self) -> None:
        if not self.data:
            raise ValueError("Frame data não pode ser vazio")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Dimensões do frame devem ser positivas")


@dataclass
class CameraStatus:
    """Estado atual da câmera."""
    is_running: bool
    device_index: int
    fps: float
    resolution: tuple[int, int]
    error: Optional[str] = None

    @property
    def is_healthy(self) -> bool:
        return self.is_running and self.error is None


@dataclass
class CaptureSession:
    """Representa uma sessão de captura ativa."""
    session_id: str
    device_index: int
    started_at: float
    frames_captured: int = 0
    errors: list[str] = field(default_factory=list)

    def record_frame(self) -> None:
        self.frames_captured += 1

    def record_error(self, error: str) -> None:
        self.errors.append(error)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
```

### `app/domain/camera/interfaces.py`
```python
from abc import ABC, abstractmethod
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


class CameraError(Exception):
    """Erro base para falhas de câmera."""
    pass


class CameraNotFoundError(CameraError):
    """Câmera não encontrada no device index especificado."""
    pass


class CameraAlreadyRunningError(CameraError):
    """Tentativa de iniciar uma câmera já em execução."""
    pass
```

## Critérios de Aceitação da Task 3.1
- [ ] Arquivos criados na estrutura correta
- [ ] `from app.domain.camera.entities import Frame` funciona sem erro
- [ ] `from app.domain.camera.interfaces import ICameraAdapter` funciona sem erro
- [ ] Nenhuma importação de OpenCV, FastAPI ou qualquer lib externa no domain
- [ ] `Frame(data=b"", width=100, height=100, timestamp=0.0)` lança `ValueError`
- [ ] `python -c "from app.domain.camera.entities import Frame, CameraStatus, CaptureSession"` roda sem erro

---

---

# TASK 3.2 — Application: Use Cases

## Objetivo
Criar os casos de uso que orquestram a câmera usando apenas a interface `ICameraAdapter`. Esta camada não conhece OpenCV nem FastAPI — apenas o domínio.

## Arquivos a Criar

```
app/application/
├── __init__.py
└── camera/
    ├── __init__.py
    └── use_cases.py
```

## Implementação

### `app/application/camera/use_cases.py`
```python
import time
import uuid
from app.domain.camera.entities import Frame, CameraStatus, CaptureSession
from app.domain.camera.interfaces import (
    ICameraAdapter,
    CameraAlreadyRunningError,
    CameraError,
)


class CameraUseCases:
    """
    Orquestra todas as operações de câmera.
    Depende apenas da interface ICameraAdapter — não conhece OpenCV.
    """

    def __init__(self, adapter: ICameraAdapter) -> None:
        self._adapter = adapter
        self._session: CaptureSession | None = None

    def start_capture(self) -> CaptureSession:
        """
        Inicia a captura. Cria e retorna uma CaptureSession.
        Lança CameraAlreadyRunningError se já estiver rodando.
        """
        if self._adapter.is_running():
            raise CameraAlreadyRunningError("Câmera já está em execução")

        self._adapter.start()
        self._session = CaptureSession(
            session_id=str(uuid.uuid4()),
            device_index=self._adapter.get_status().device_index,
            started_at=time.time(),
        )
        return self._session

    def stop_capture(self) -> None:
        """Para a captura e encerra a sessão atual."""
        self._adapter.stop()
        self._session = None

    def get_current_frame(self) -> Frame | None:
        """Retorna o frame mais recente. None se câmera parada ou sem frame."""
        if not self._adapter.is_running():
            return None
        return self._adapter.get_frame()

    def get_status(self) -> CameraStatus:
        """Retorna o status atual da câmera."""
        return self._adapter.get_status()

    def get_session(self) -> CaptureSession | None:
        """Retorna a sessão ativa ou None."""
        return self._session

    def is_capturing(self) -> bool:
        return self._adapter.is_running()
```

## Critérios de Aceitação da Task 3.2
- [ ] Arquivos criados
- [ ] `from app.application.camera.use_cases import CameraUseCases` funciona
- [ ] Nenhuma importação de OpenCV, FastAPI ou SQLAlchemy
- [ ] `CameraUseCases` aceita qualquer objeto que implemente `ICameraAdapter`
- [ ] Chamar `start_capture()` duas vezes lança `CameraAlreadyRunningError`

---

---

# TASK 3.3 — Infrastructure: Adaptador OpenCV

## Objetivo
Criar a implementação concreta de `ICameraAdapter` usando OpenCV. Esta é a única camada que conhece OpenCV. Toda a complexidade de threading e captura fica aqui.

## Pré-requisito
```bash
# Adicionar ao pyproject.toml e rodar:
uv add opencv-python-headless
```

## Arquivos a Criar

```
app/infrastructure/
├── __init__.py
└── camera/
    ├── __init__.py
    └── opencv_adapter.py
```

## Implementação

### `app/infrastructure/camera/opencv_adapter.py`
```python
import threading
import time
import cv2
import numpy as np
from app.domain.camera.entities import Frame, CameraStatus
from app.domain.camera.interfaces import (
    ICameraAdapter,
    CameraError,
    CameraNotFoundError,
)
from app.config import settings


class OpenCVCameraAdapter(ICameraAdapter):
    """
    Implementação concreta de ICameraAdapter usando OpenCV.
    Captura frames em thread separada para não bloquear a API.
    """

    def __init__(self) -> None:
        self._cap: cv2.VideoCapture | None = None
        self._latest_frame: Frame | None = None
        self._is_running: bool = False
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._error: str | None = None
        self._device_index = settings.camera_device_index

    def start(self) -> None:
        """Abre a câmera e inicia a thread de captura."""
        cap = cv2.VideoCapture(self._device_index)

        if not cap.isOpened():
            raise CameraNotFoundError(
                f"Câmera não encontrada no device index {self._device_index}"
            )

        cap.set(cv2.CAP_PROP_FPS, settings.camera_fps)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.camera_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.camera_height)

        self._cap = cap
        self._is_running = True
        self._error = None

        self._thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="camera-capture-thread",
        )
        self._thread.start()

    def stop(self) -> None:
        """Para a thread de captura e libera recursos."""
        self._is_running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        if self._cap:
            self._cap.release()
            self._cap = None

        with self._lock:
            self._latest_frame = None

    def get_frame(self) -> Frame | None:
        """Retorna o frame mais recente de forma thread-safe."""
        with self._lock:
            return self._latest_frame

    def get_status(self) -> CameraStatus:
        actual_fps = 0.0
        resolution = (0, 0)

        if self._cap and self._cap.isOpened():
            actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            resolution = (w, h)

        return CameraStatus(
            is_running=self._is_running,
            device_index=self._device_index,
            fps=actual_fps,
            resolution=resolution,
            error=self._error,
        )

    def is_running(self) -> bool:
        return self._is_running

    def _capture_loop(self) -> None:
        """
        Loop de captura rodando em thread separada.
        Captura frames continuamente e atualiza _latest_frame.
        """
        interval = 1.0 / settings.camera_fps

        while self._is_running:
            start = time.monotonic()

            if not self._cap or not self._cap.isOpened():
                self._error = "Câmera desconectada durante captura"
                self._is_running = False
                break

            ret, raw_frame = self._cap.read()

            if not ret:
                self._error = "Falha ao ler frame da câmera"
                continue

            encode_params = [cv2.IMWRITE_JPEG_QUALITY, settings.camera_jpeg_quality]
            success, buffer = cv2.imencode(".jpg", raw_frame, encode_params)

            if not success:
                continue

            frame = Frame(
                data=buffer.tobytes(),
                width=raw_frame.shape[1],
                height=raw_frame.shape[0],
                timestamp=time.time(),
            )

            with self._lock:
                self._latest_frame = frame

            # Controle de FPS
            elapsed = time.monotonic() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
```

## Critérios de Aceitação da Task 3.3
- [ ] `uv add opencv-python-headless` concluído sem erros
- [ ] `from app.infrastructure.camera.opencv_adapter import OpenCVCameraAdapter` funciona
- [ ] `OpenCVCameraAdapter` implementa todos os métodos de `ICameraAdapter`
- [ ] Thread de captura é `daemon=True` (morre com o processo principal)
- [ ] `_lock` protege acesso a `_latest_frame`
- [ ] Nenhuma importação de FastAPI ou SQLAlchemy neste arquivo

---

---

# TASK 3.4 — Interface: Rotas FastAPI + Stream MJPEG

## Objetivo
Criar as rotas FastAPI que expõem a câmera via HTTP. O stream MJPEG é o mecanismo que permite ao frontend exibir o vídeo ao vivo com um simples `<img src="...">`.

## Conceito: MJPEG Stream
```
HTTP Response com Content-Type: multipart/x-mixed-replace
Cada "parte" é um JPEG encodado precedido por headers:
--frame
Content-Type: image/jpeg
Content-Length: <tamanho>

<bytes do JPEG>
```
O browser entende esse formato e atualiza a imagem automaticamente — sem WebSocket, sem polling.

## Arquivos a Criar/Modificar

```
app/camera/
├── __init__.py
├── router.py
├── schemas.py
└── dependencies.py

app/main.py          ← MODIFICAR: registrar router + iniciar câmera no lifespan
```

### `app/camera/dependencies.py`
```python
from functools import lru_cache
from app.application.camera.use_cases import CameraUseCases
from app.infrastructure.camera.opencv_adapter import OpenCVCameraAdapter


@lru_cache(maxsize=1)
def get_camera_use_cases() -> CameraUseCases:
    """
    Retorna instância singleton de CameraUseCases.
    lru_cache garante que apenas uma instância existe durante o ciclo de vida da app.
    """
    adapter = OpenCVCameraAdapter()
    return CameraUseCases(adapter=adapter)
```

### `app/camera/schemas.py`
```python
from pydantic import BaseModel
from typing import Optional


class CameraStatusResponse(BaseModel):
    is_running: bool
    device_index: int
    fps: float
    resolution: tuple[int, int]
    error: Optional[str] = None
    is_healthy: bool


class CaptureSessionResponse(BaseModel):
    session_id: str
    device_index: int
    started_at: float
    frames_captured: int
    has_errors: bool


class MessageResponse(BaseModel):
    message: str
```

### `app/camera/router.py`
```python
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.application.camera.use_cases import CameraUseCases
from app.camera.dependencies import get_camera_use_cases
from app.camera.schemas import CameraStatusResponse, MessageResponse
from app.core.security import get_current_user
from app.domain.camera.interfaces import CameraAlreadyRunningError, CameraError

router = APIRouter(prefix="/camera", tags=["camera"])


@router.post("/start", response_model=MessageResponse)
def start_camera(
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
    _: str = Depends(get_current_user),
):
    """Inicia a captura da câmera."""
    try:
        use_cases.start_capture()
        return MessageResponse(message="Câmera iniciada com sucesso")
    except CameraAlreadyRunningError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Câmera já está em execução",
        )
    except CameraError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.post("/stop", response_model=MessageResponse)
def stop_camera(
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
    _: str = Depends(get_current_user),
):
    """Para a captura da câmera."""
    use_cases.stop_capture()
    return MessageResponse(message="Câmera parada")


@router.get("/status", response_model=CameraStatusResponse)
def get_camera_status(
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
    _: str = Depends(get_current_user),
):
    """Retorna o status atual da câmera."""
    status_obj = use_cases.get_status()
    return CameraStatusResponse(
        is_running=status_obj.is_running,
        device_index=status_obj.device_index,
        fps=status_obj.fps,
        resolution=status_obj.resolution,
        error=status_obj.error,
        is_healthy=status_obj.is_healthy,
    )


@router.get("/stream")
async def stream_camera(
    use_cases: CameraUseCases = Depends(get_camera_use_cases),
    _: str = Depends(get_current_user),
):
    """
    Stream MJPEG ao vivo da câmera.
    Compatível com <img src="/camera/stream"> no frontend.
    """
    if not use_cases.is_capturing():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Câmera não está em execução. Chame POST /camera/start primeiro.",
        )

    async def frame_generator():
        while True:
            frame = use_cases.get_current_frame()
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(frame.data)).encode() + b"\r\n"
                    b"\r\n" + frame.data + b"\r\n"
                )
            await asyncio.sleep(1 / 15)  # ~15 FPS

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
```

### Modificar `app/main.py` — adicionar ao lifespan e registrar router
```python
# No lifespan, adicionar após create_all:
from app.camera.dependencies import get_camera_use_cases

# Pré-aquecer a dependência singleton
get_camera_use_cases()

# No registro de routers, adicionar:
from app.camera.router import router as camera_router
app.include_router(camera_router)
```

## Critérios de Aceitação da Task 3.4
- [ ] `GET /camera/status` retorna JSON com status da câmera (sem iniciar)
- [ ] `POST /camera/start` inicia a câmera (is_running: true)
- [ ] `POST /camera/stop` para a câmera
- [ ] `GET /camera/stream` retorna `Content-Type: multipart/x-mixed-replace`
- [ ] `GET /camera/stream` sem câmera iniciada retorna 409
- [ ] Todas as rotas retornam 401 sem token JWT
- [ ] Swagger em `/docs` mostra as 4 novas rotas

---

---

# TASK 3.5 — Frontend: Preview ao Vivo no Dashboard

## Objetivo
Atualizar o Dashboard para exibir o preview da câmera ao vivo, com controles de iniciar/parar e indicador de status.

## Arquivos a Criar/Modificar

```
src/
├── services/
│   └── cameraService.ts      ← NOVO
├── hooks/
│   └── useCameraStatus.ts    ← NOVO
└── pages/
    └── DashboardPage.tsx     ← MODIFICAR
```

### `src/services/cameraService.ts`
```typescript
import { apiFetch } from '@/lib/api'

export interface CameraStatus {
  is_running: boolean
  device_index: number
  fps: number
  resolution: [number, number]
  error: string | null
  is_healthy: boolean
}

export const cameraService = {
  getStatus: () => apiFetch<CameraStatus>('/camera/status'),
  start: () => apiFetch<{ message: string }>('/camera/start', { method: 'POST' }),
  stop: () => apiFetch<{ message: string }>('/camera/stop', { method: 'POST' }),
  getStreamUrl: () => `${import.meta.env.VITE_API_URL}/camera/stream`,
}
```

### `src/hooks/useCameraStatus.ts`
```typescript
import { useState, useEffect, useCallback } from 'react'
import { cameraService, CameraStatus } from '@/services/cameraService'

export function useCameraStatus(pollIntervalMs = 3000) {
  const [status, setStatus] = useState<CameraStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      const data = await cameraService.getStatus()
      setStatus(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar status')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, pollIntervalMs)
    return () => clearInterval(interval)
  }, [fetchStatus, pollIntervalMs])

  return { status, isLoading, error, refetch: fetchStatus }
}
```

### Atualizar `src/pages/DashboardPage.tsx`

O Dashboard deve ter:

1. **Header:** título "Sports Highlights" + botão "Sair"
2. **Painel de status:** badge verde/vermelho indicando se câmera está rodando
3. **Preview ao vivo:** `<img>` apontando para o stream MJPEG (apenas quando câmera iniciada)
4. **Controles:** botões "Iniciar Câmera" e "Parar Câmera"
5. **Estado de erro:** mensagem clara se câmera não encontrada

```typescript
// Lógica de exibição do stream:
// - Se câmera rodando: <img src={streamUrl} /> com width 100%
// - Se câmera parada: placeholder cinza com ícone e texto "Câmera parada"
// - O token JWT deve ser incluído via header — MAS img src não suporta headers.
//
// SOLUÇÃO para auth no stream:
// O endpoint /camera/stream deve aceitar token via query param ?token=<jwt>
// no MVP (aceitável para uso local). Adicionar no router.py:
// token: str = Query(...) e validar manualmente.
// Alternativa futura: cookie httpOnly.

// URL do stream com token:
const token = getAuthToken() // exportar função de api.ts
const streamUrl = `${cameraService.getStreamUrl()}?token=${token}`
```

> **NOTA IMPORTANTE PARA O AGY:**
> O `<img src>` do browser não envia headers customizados. Para autenticar o stream,
> modificar o endpoint `/camera/stream` para aceitar o token via query parameter:
> `GET /camera/stream?token=<jwt>`
> Adicionar `token: str = Query(...)` na rota e validar com `verify_token()`.
> Exportar `getAuthToken()` de `src/lib/api.ts` para o frontend usar.

## Critérios de Aceitação da Task 3.5
- [ ] Dashboard exibe status da câmera (rodando / parada)
- [ ] Botão "Iniciar Câmera" chama `POST /camera/start`
- [ ] Botão "Parar Câmera" chama `POST /camera/stop`
- [ ] Quando câmera iniciada, `<img>` exibe o stream ao vivo
- [ ] Quando câmera parada, placeholder é exibido
- [ ] Status atualiza automaticamente a cada 3 segundos
- [ ] Sem erros no console do browser
- [ ] Token é passado corretamente para o stream

---

---

## 🧪 Critérios de Aceitação da Fase 3 Completa

Só considerar a Fase 3 concluída quando **todos** os itens abaixo forem verdadeiros:

### Backend
- [x] `uv run uvicorn app.main:app --reload` inicia sem erros
- [x] `GET /camera/status` retorna JSON válido sem câmera iniciada
- [x] `POST /camera/start` inicia captura (is_running: true)
- [x] `GET /camera/stream?token=<jwt>` retorna stream MJPEG
- [x] `POST /camera/stop` para a câmera (is_running: false)
- [x] Nenhum erro no terminal durante captura contínua por 30 segundos
- [x] Thread da câmera é `daemon=True`
- [x] Importações respeitam a hierarquia de camadas

### Frontend
- [x] Dashboard exibe preview ao vivo após "Iniciar Câmera"
- [x] Placeholder exibido quando câmera parada
- [x] Status badge atualiza corretamente
- [x] Sem erros no console do browser
- [x] `npm run build` passa sem erros TypeScript

### Arquitetura
- [x] `domain/` não importa nada externo ao projeto
- [x] `application/` não importa OpenCV, FastAPI ou SQLAlchemy
- [x] `infrastructure/` não importa FastAPI
- [x] `camera/router.py` não importa OpenCV diretamente

---

## 🚨 Problemas Comuns e Soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| `CameraNotFoundError: device index 0` | Webcam não detectada | Testar `cv2.VideoCapture(1)` ou verificar permissões |
| Stream trava após ~30s | Thread morreu silenciosamente | Verificar logs, checar `_error` no status |
| `<img>` não exibe stream | Token inválido no query param | Verificar se `getAuthToken()` retorna o token correto |
| Alto uso de CPU | FPS muito alto | Reduzir `CAMERA_FPS=10` no `.env` |
| Frame preto | Câmera ocupada por outro processo | Fechar outros apps usando webcam |
| CORS error no stream | Origin não permitida | Verificar `allow_origins` no `main.py` |

---

## 📝 Notas de Arquitetura para o Desenvolvedor

### Por que threading e não asyncio na captura?
OpenCV (`cv2.VideoCapture.read()`) é uma operação **bloqueante síncrona**. Se rodasse na event loop do asyncio, travaria toda a API durante a leitura. Com uma thread daemon separada, a captura acontece em paralelo sem bloquear as requisições HTTP.

### Por que `lru_cache` no `get_camera_use_cases()`?
FastAPI cria uma nova instância de dependência por requisição por padrão. Com `lru_cache(maxsize=1)`, garantimos que existe **apenas uma instância** de `CameraUseCases` e `OpenCVCameraAdapter` durante todo o ciclo de vida da aplicação — essencial porque temos estado (a thread de captura e o frame mais recente).

### Por que MJPEG e não WebSocket?
MJPEG é mais simples: funciona com uma tag `<img>` nativa do browser, sem JavaScript extra. WebSocket seria necessário para latências subsecond ou comunicação bidirecional — não é o caso aqui. MJPEG com 15 FPS é perfeito para preview ao vivo de quadra esportiva.

### Por que token via query param no stream?
`<img src>` não suporta headers customizados — é limitação do browser. No MVP local, query param é aceitável. Em produção futura, a solução correta é um cookie `httpOnly` com o JWT, que o browser envia automaticamente em toda requisição, incluindo `<img src>`.

