# Fase 6 — TTL Automático (Limpeza de Vídeos Expirados)
## Arquivo de Referência do Antigravity CLI

> **INSTRUÇÃO PARA O AGY:** Este arquivo é sua fonte de verdade durante toda a Fase 6.
> Consulte-o antes de iniciar cada minitarefa. Nunca pule uma task sem concluir a anterior.
> As Fases 3, 4 e 5 devem estar 100% concluídas antes de iniciar esta fase.
> Ao concluir cada task, marque o checkbox correspondente neste documento.

---

## 🗺️ Visão Geral da Fase

### Objetivo
Implementar limpeza automática de vídeos expirados: um job periódico que roda dentro do
processo FastAPI, verifica vídeos que atingiram seu TTL ou foram deletados manualmente,
apaga os arquivos físicos do disco e remove os registros do banco.

### O Que Esta Fase Entrega
- Dependência `APScheduler` integrada ao ciclo de vida do FastAPI
- Job de limpeza que roda a cada hora (configurável)
- Limpeza de arquivos físicos + remoção do banco (hard delete)
- Limpeza de arquivos temporários órfãos em `storage/temp/`
- Endpoint `GET /admin/ttl/status` para monitorar o último job
- Log estruturado de cada execução (quantos arquivos deletados, espaço liberado)
- Execução manual via `POST /admin/ttl/run` (para testes)

### O Que Esta Fase NÃO Entrega
- Interface visual do TTL no frontend
- Configuração de TTL por vídeo individual
- Notificações ao usuário quando um vídeo expira
- Histórico de limpezas no banco de dados

### Pré-requisitos
- Fase 5 concluída (galeria funcionando, soft delete implementado)
- `app/videos/models.py` com colunas `expires_at`, `is_deleted` e `file_path`
- Diretório `storage/videos/` existente com ao menos um vídeo para testar

---

## 🏗️ Arquitetura da Fase 6

```
backend/
└── app/
    ├── domain/
    │   └── camera/
    │       └── interfaces.py     ← MODIFICAR: adicionar ITTLService
    │
    ├── application/
    │   └── ttl/
    │       ├── __init__.py
    │       └── use_cases.py      ← NOVO: CleanExpiredVideosUseCase
    │
    ├── infrastructure/
    │   └── scheduler/
    │       ├── __init__.py
    │       └── apscheduler.py    ← NOVO: setup do APScheduler + job registration
    │
    ├── admin/                    ← NOVO: router de administração
    │   ├── __init__.py
    │   ├── router.py             ← GET /admin/ttl/status, POST /admin/ttl/run
    │   └── schemas.py            ← TTLStatusResponse, TTLRunResponse
    │
    └── main.py                   ← MODIFICAR: iniciar/parar scheduler no lifespan
```

### Dois Caminhos de Deleção — NUNCA Confundir

```
CAMINHO 1 — Soft Delete Manual (Fase 5, já implementado):
  Usuário clica "Deletar" na galeria
        ↓
  DELETE /videos/{id}
        ↓
  video.is_deleted = True   ← apenas flag no banco
  arquivo físico: INTACTO   ← permanece no disco

CAMINHO 2 — Hard Delete por TTL (Fase 6, esta fase):
  Job periódico acorda
        ↓
  Busca: is_deleted=True OU expires_at < now()
        ↓
  os.remove(video.file_path)   ← apaga arquivo físico
        ↓
  db.delete(video)             ← remove registro do banco
```

### Regras de Dependência (NUNCA violar)
```
domain              → não importa nada do projeto
application/ttl     → importa domain + models + config
infrastructure/scheduler → importa application + APScheduler
admin/router        → importa application + schemas
main.py             → importa infrastructure/scheduler
```

---

## 📋 Estado de Progresso

> **AGY:** Atualize os checkboxes conforme completar cada task.

- [ ] **Task 6.1** — Domain: Interface ITTLService e entidade CleanupResult
- [ ] **Task 6.2** — Application: CleanExpiredVideosUseCase
- [ ] **Task 6.3** — Infrastructure: APScheduler setup e integração com lifespan
- [ ] **Task 6.4** — Interface: Router /admin com status e execução manual

---

## 🔗 Contratos Entre Camadas

> **AGY:** Estes contratos são imutáveis. Todas as tasks devem respeitá-los.

### CleanupResult
```python
@dataclass
class CleanupResult:
    """Resultado de uma execução do job de limpeza."""
    started_at: float
    completed_at: float
    videos_deleted: int          # registros removidos do banco
    files_deleted: int           # arquivos físicos removidos do disco
    files_missing: int           # registros cujo arquivo já não existia em disco
    temp_files_deleted: int      # arquivos órfãos em storage/temp/ removidos
    bytes_freed: int             # espaço total liberado em bytes
    errors: list[str]            # erros não-fatais durante a execução

    @property
    def duration_seconds(self) -> float:
        return self.completed_at - self.started_at

    @property
    def mb_freed(self) -> float:
        return self.bytes_freed / (1024 * 1024)

    @property
    def had_errors(self) -> bool:
        return len(self.errors) > 0
```

### ITTLService
```python
class ITTLService(ABC):
    @abstractmethod
    def run_cleanup(self) -> CleanupResult:
        """
        Executa limpeza completa:
        1. Vídeos com expires_at < now()
        2. Vídeos com is_deleted=True
        3. Arquivos órfãos em storage/temp/
        Nunca lança exceção — erros vão para CleanupResult.errors.
        """
        ...

    @abstractmethod
    def get_last_result(self) -> CleanupResult | None:
        """Retorna o resultado da última execução ou None se nunca rodou."""
        ...
```

### Endpoints
```
GET /admin/ttl/status
  Auth: Bearer token obrigatório
  Response: {
    "last_run_at": "2024-01-15T10:30:00",  ← None se nunca rodou
    "next_run_at": "2024-01-15T11:30:00",
    "videos_deleted": 3,
    "files_deleted": 3,
    "bytes_freed": 157286400,
    "mb_freed": 150.0,
    "duration_seconds": 0.42,
    "had_errors": false,
    "errors": []
  }

POST /admin/ttl/run
  Auth: Bearer token obrigatório
  Response: TTLRunResponse (resultado imediato da execução)
  Comportamento: executa o job AGORA, de forma síncrona, e retorna o resultado
  Uso: testes manuais e debugging
```

---

## ⚙️ Novas Configurações

> **AGY:** Adicionar ao `.env` e ao `app/config.py` antes de iniciar a Task 6.2.

```env
# TTL
TTL_DAYS=7
TTL_RUN_INTERVAL_HOURS=1
TTL_TEMP_MAX_AGE_HOURS=24
```

```python
# Em app/config.py — adicionar à classe Settings:
ttl_days: int = 7
ttl_run_interval_hours: int = 1
ttl_temp_max_age_hours: int = 24
```

---

## 📦 Nova Dependência

> **AGY:** Adicionar ao `pyproject.toml` e rodar `uv sync` antes da Task 6.3.

```toml
dependencies = [
    # ... existentes ...
    "apscheduler>=3.10.0",
]
```

> Usar APScheduler 3.x (não 4.x — a API mudou significativamente na v4).
> Verificar: `uv run python -c "import apscheduler; print(apscheduler.__version__)"`

---

---

# TASK 6.1 — Domain: CleanupResult e ITTLService

## Objetivo
Adicionar ao domínio a entidade `CleanupResult` e a interface `ITTLService`. Esta camada
não conhece APScheduler, SQLAlchemy ou o sistema de arquivos — apenas define os contratos.

## Arquivos a Modificar

```
app/domain/camera/
├── entities.py     ← MODIFICAR: adicionar CleanupResult
└── interfaces.py   ← MODIFICAR: adicionar ITTLService
```

## Implementação

### Adicionar em `app/domain/camera/entities.py`

```python
# Adicionar ao final do arquivo, após as entidades existentes:

@dataclass
class CleanupResult:
    """
    Resultado de uma execução do job de limpeza de vídeos expirados.
    Imutável após criação — representa um snapshot do que aconteceu.
    """
    started_at: float
    completed_at: float
    videos_deleted: int
    files_deleted: int
    files_missing: int
    temp_files_deleted: int
    bytes_freed: int
    errors: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return self.completed_at - self.started_at

    @property
    def mb_freed(self) -> float:
        return round(self.bytes_freed / (1024 * 1024), 2)

    @property
    def had_errors(self) -> bool:
        return len(self.errors) > 0

    def to_log_line(self) -> str:
        """Formata resultado como linha de log legível."""
        return (
            f"TTL cleanup concluído em {self.duration_seconds:.2f}s: "
            f"{self.videos_deleted} vídeos removidos, "
            f"{self.files_deleted} arquivos deletados, "
            f"{self.mb_freed:.1f} MB liberados"
            + (f", {len(self.errors)} erros" if self.had_errors else "")
        )
```

### Adicionar em `app/domain/camera/interfaces.py`

```python
# Adicionar ao final do arquivo, após as interfaces existentes:

class ITTLService(ABC):
    """
    Contrato para o serviço de limpeza automática de vídeos expirados.
    Implementação concreta fica em application/ttl/use_cases.py.
    """

    @abstractmethod
    def run_cleanup(self) -> "CleanupResult":
        """
        Executa limpeza completa de vídeos expirados e deletados.
        NUNCA lança exceção — todos os erros são capturados em CleanupResult.errors.
        Garante que o sistema continua funcionando mesmo se um arquivo não puder ser deletado.
        """
        ...

    @abstractmethod
    def get_last_result(self) -> Optional["CleanupResult"]:
        """
        Retorna o resultado da última execução bem-sucedida.
        Retorna None se o job nunca foi executado desde o início do servidor.
        """
        ...
```

## Critérios de Aceitação da Task 6.1
- [ ] `from app.domain.camera.entities import CleanupResult` funciona
- [ ] `from app.domain.camera.interfaces import ITTLService` funciona
- [ ] `CleanupResult.to_log_line()` retorna string legível
- [ ] `CleanupResult.mb_freed` converte bytes corretamente
- [ ] Nenhuma importação de APScheduler, SQLAlchemy ou `os` no domain

---

---

# TASK 6.2 — Application: CleanExpiredVideosUseCase

## Objetivo
Implementar a lógica de limpeza: buscar vídeos candidatos no banco, apagar arquivos físicos,
remover registros, limpar arquivos temporários órfãos. Esta camada conhece SQLAlchemy e `os`,
mas não conhece APScheduler nem FastAPI.

## Arquivos a Criar

```
app/application/ttl/
├── __init__.py
└── use_cases.py    ← NOVO
```

## Implementação

### `app/application/ttl/use_cases.py`

```python
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
                    modified = datetime.utcfromtimestamp(entry.stat().st_mtime)
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
```

## Critérios de Aceitação da Task 6.2
- [ ] `from app.application.ttl.use_cases import ttl_use_case` funciona
- [ ] `ttl_use_case.run_cleanup()` retorna `CleanupResult` sem lançar exceção
- [ ] Vídeo com `expires_at` no passado é removido do banco e do disco
- [ ] Vídeo com `is_deleted=True` é removido do banco e do disco
- [ ] Se arquivo não existe em disco, `files_missing` é incrementado mas execução continua
- [ ] `get_last_result()` retorna `None` antes da primeira execução
- [ ] Nenhuma importação de APScheduler ou FastAPI neste arquivo
- [ ] Cria sua própria `SessionLocal()` — não depende de `Depends(get_db)`

---

---

# TASK 6.3 — Infrastructure: APScheduler Setup e Integração com Lifespan

## Objetivo
Configurar o APScheduler para rodar o job de limpeza periodicamente dentro do processo
FastAPI. O scheduler deve iniciar no startup e parar graciosamente no shutdown via `lifespan`.

## Pré-requisito

```bash
# Adicionar ao pyproject.toml e rodar:
uv add "apscheduler>=3.10.0,<4.0.0"
```

## Arquivos a Criar/Modificar

```
app/infrastructure/scheduler/
├── __init__.py
└── apscheduler.py    ← NOVO

app/main.py           ← MODIFICAR: integrar scheduler no lifespan
```

## Implementação

### `app/infrastructure/scheduler/apscheduler.py`

```python
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.application.ttl.use_cases import ttl_use_case
from app.config import settings

logger = logging.getLogger(__name__)


def _run_ttl_job() -> None:
    """
    Função executada pelo scheduler periodicamente.
    Wrapper fino — toda a lógica fica no use case.
    """
    logger.info("APScheduler: disparando job de limpeza TTL")
    try:
        result = ttl_use_case.run_cleanup()
        if result.had_errors:
            logger.warning(
                f"APScheduler: job concluído com {len(result.errors)} erro(s)"
            )
    except Exception as e:
        # Nunca deixar uma exceção vazar para o APScheduler —
        # isso faria o scheduler parar de agendar futuras execuções
        logger.exception(f"APScheduler: erro inesperado no job TTL: {e}")


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
```

### Modificar `app/main.py` — integrar scheduler no lifespan

```python
# Adicionar import:
from app.infrastructure.scheduler.apscheduler import scheduler

# Modificar o bloco lifespan para incluir o scheduler.
# O lifespan já existe da Fase 1 — apenas adicionar as linhas do scheduler:

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # Banco de dados
    Base.metadata.create_all(bind=engine)

    # Scheduler de limpeza TTL
    scheduler.start()
    logger.info("Scheduler iniciado")

    yield

    # --- SHUTDOWN ---
    scheduler.shutdown(wait=False)
    logger.info("Scheduler encerrado")
```

> **NOTA PARA O AGY:** `wait=False` no shutdown é intencional. Evita que o servidor
> fique travado aguardando a conclusão de um job de limpeza durante o encerramento.
> O job de limpeza é idempotente — rodar na próxima inicialização não causa problemas.

## Critérios de Aceitação da Task 6.3
- [ ] `uv sync` inclui `apscheduler` sem erros
- [ ] `uv run uvicorn app.main:app --reload` inicia sem erros
- [ ] Log de startup mostra: `"Scheduler iniciado"`
- [ ] Log de startup mostra: `"Scheduler configurado: job TTL a cada 1h"`
- [ ] Ctrl+C no servidor mostra: `"Scheduler encerrado"`
- [ ] `scheduler.get_jobs()` retorna 1 job com id `"ttl_cleanup"`
- [ ] `max_instances=1` garante que duas limpezas não rodam simultaneamente
- [ ] `coalesce=True` garante que execuções perdidas não se acumulam

---

---

# TASK 6.4 — Interface: Router /admin com Status e Execução Manual

## Objetivo
Expor endpoints de administração para monitorar o TTL e disparar execução manual.
Útil para testar sem esperar 1 hora pelo scheduler, e para verificar o estado do sistema.

## Arquivos a Criar/Modificar

```
app/admin/
├── __init__.py
├── router.py       ← NOVO
└── schemas.py      ← NOVO

app/main.py         ← MODIFICAR: registrar router de admin
```

## Implementação

### `app/admin/schemas.py`

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TTLStatusResponse(BaseModel):
    scheduler_running: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[float]
    last_duration_seconds: Optional[float]
    last_videos_deleted: Optional[int]
    last_files_deleted: Optional[int]
    last_files_missing: Optional[int]
    last_temp_files_deleted: Optional[int]
    last_mb_freed: Optional[float]
    last_had_errors: Optional[bool]
    last_errors: Optional[list[str]]


class TTLRunResponse(BaseModel):
    started_at: float
    completed_at: float
    duration_seconds: float
    videos_deleted: int
    files_deleted: int
    files_missing: int
    temp_files_deleted: int
    mb_freed: float
    had_errors: bool
    errors: list[str]
```

### `app/admin/router.py`

```python
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
```

### Modificar `app/main.py` — registrar router de admin

```python
# Adicionar import:
from app.admin.router import router as admin_router

# Adicionar ao registro de routers:
app.include_router(admin_router)
```

## Critérios de Aceitação da Task 6.4
- [ ] `GET /admin/ttl/status` retorna `scheduler_running: true`
- [ ] `GET /admin/ttl/status` retorna `next_run_at` com o horário da próxima execução
- [ ] `GET /admin/ttl/status` retorna `last_*: null` antes da primeira execução
- [ ] `POST /admin/ttl/run` executa o job e retorna `TTLRunResponse`
- [ ] `POST /admin/ttl/run` com vídeos expirados retorna `videos_deleted > 0`
- [ ] Ambas as rotas retornam 401 sem Bearer token
- [ ] Swagger em `/docs` mostra as rotas sob a tag `admin`

---

---

## 🧪 Critérios de Aceitação da Fase 6 Completa

Só considerar a Fase 6 concluída quando **todos** os itens abaixo forem verdadeiros:

### Fluxo End-to-End do TTL Natural
- [ ] Criar vídeo com `expires_at = datetime.utcnow() - timedelta(minutes=1)` diretamente no banco
- [ ] `POST /admin/ttl/run` remove o vídeo do banco e do disco
- [ ] `GET /videos` não retorna mais o vídeo removido
- [ ] `GET /admin/ttl/status` mostra `last_videos_deleted: 1`

### Fluxo End-to-End do Soft Delete + TTL
- [ ] Deletar vídeo pela galeria (Fase 5) → `is_deleted=True` no banco
- [ ] Arquivo ainda existe em disco após soft delete
- [ ] `POST /admin/ttl/run` remove o arquivo do disco e o registro do banco
- [ ] `GET /videos` confirma que vídeo não existe mais

### Limpeza de Temporários
- [ ] Criar arquivo em `storage/temp/` com data de modificação antiga
- [ ] `POST /admin/ttl/run` remove o arquivo temporário
- [ ] `GET /admin/ttl/status` mostra `last_temp_files_deleted: 1`

### Resiliência
- [ ] Remover manualmente um arquivo de vídeo do disco (simular disco corrompido)
- [ ] `POST /admin/ttl/run` não lança exceção — `files_missing: 1`, `errors: []`
- [ ] Registro do banco é removido mesmo quando arquivo não existe em disco
- [ ] Servidor não trava ou reinicia durante execução do job

### Scheduler
- [ ] Servidor inicia com log: `"Scheduler iniciado"`
- [ ] `GET /admin/ttl/status` mostra `scheduler_running: true` e `next_run_at`
- [ ] Ctrl+C para o servidor mostrando `"Scheduler encerrado"` sem travar
- [ ] Restart do servidor não cria jobs duplicados (`replace_existing=True`)

### Qualidade
- [ ] `CleanExpiredVideosUseCase` não importa FastAPI
- [ ] `apscheduler.py` não importa SQLAlchemy diretamente
- [ ] `admin/router.py` não contém lógica de negócio — apenas delega ao use case
- [ ] Todos os erros são capturados e logados, nunca silenciados

---

## 🚨 Problemas Comuns e Soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| `ImportError: apscheduler` | Dependência não instalada | Rodar `uv sync` após adicionar ao `pyproject.toml` |
| Job não aparece em `get_jobs()` | `create_scheduler()` não foi chamado | Verificar importação de `scheduler` em `main.py` |
| Servidor trava no shutdown | `scheduler.shutdown(wait=True)` | Usar `wait=False` no shutdown |
| Job roda duas vezes simultâneo | `max_instances` não definido | Garantir `max_instances=1` no `job_defaults` |
| `OperationalError: database is locked` | Duas threads acessando SQLite simultaneamente | `check_same_thread=False` já está em `database.py` — verificar se está correto |
| Arquivo não deletado mas sem erro | Permissão de arquivo negada | Verificar permissões do diretório `storage/videos/` |
| `next_run_at: null` no status | Scheduler não iniciado | Verificar se `scheduler.start()` está no lifespan |
| Erros de fuso horário no `next_run_at` | APScheduler usa timezone-aware | Adicionar `timezone='UTC'` ao `BackgroundScheduler` se necessário |

---

## 📝 Notas de Arquitetura para o Desenvolvedor

### Por que APScheduler e não cron do sistema operacional?
Cron exigiria configuração específica por OS (diferente no Windows, Linux e macOS), acesso
ao ambiente do sistema, e o script de limpeza precisaria de sua própria conexão com o banco.
APScheduler roda dentro do processo Python, reutiliza toda a configuração existente, e é
portável entre sistemas operacionais — essencial para um produto que será instalado em
máquinas de clientes com sistemas variados.

### Por que `coalesce=True` no scheduler?
Se o servidor ficou offline por 3 horas e voltou, sem `coalesce=True` o APScheduler tentaria
rodar 3 execuções em sequência para compensar o tempo perdido. Com `coalesce=True`, ele
executa apenas uma vez e segue o ritmo normal. Para limpeza de TTL, uma única execução
é suficiente — executar 3 vezes seguidas não adiciona valor.

### Por que o job cria sua própria `SessionLocal()`?
O job do APScheduler roda em uma thread separada, fora do contexto de qualquer requisição
HTTP. Não existe uma `Session` ativa que possa ser injetada via `Depends`. Por isso o use
case cria e fecha sua própria session explicitamente, garantindo que a conexão seja liberada
ao final de cada execução.

### Por que hard delete no TTL e soft delete manual?
O soft delete na galeria é uma operação do usuário — deve ser reversível em caso de erro
de interface. O TTL é uma operação automática e definitiva — quando um vídeo expirou, ele
não volta mais. Manter os dois caminhos separados torna o código mais fácil de auditar:
"o arquivo foi removido pelo usuário ou pelo sistema?"

### Por que `POST /admin/ttl/run` é síncrono e não usa BackgroundTasks?
Para debugging e testes, você precisa ver o resultado imediatamente na resposta. Um endpoint
assíncrono retornaria um job_id e você teria que fazer polling — que é o padrão certo para
operações longas como salvar vídeo, mas excessivo para uma limpeza que dura menos de 1 segundo.

