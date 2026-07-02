# Fase 7 — Polish de Backend + Logs + README
## Arquivo de Referência do Antigravity CLI

> **INSTRUÇÃO PARA O AGY:** Este arquivo é sua fonte de verdade durante toda a Fase 7.
> Consulte-o antes de iniciar cada minitarefa. Nunca pule uma task sem concluir a anterior.
> Todas as fases anteriores (3–6) devem estar concluídas antes de iniciar esta fase.
> Esta é a fase final do MVP. Ao concluir, o produto está pronto para demonstração.
> Ao concluir cada task, marque o checkbox correspondente neste documento.

---

## 🗺️ Visão Geral da Fase

### Objetivo
Fechar o MVP com qualidade de produção: erros do backend tratados e logados de forma
rastreável, comportamentos inesperados visíveis nos logs, e documentação de instalação
completa para configurar o produto do zero em qualquer máquina.

### O Que Esta Fase Entrega
- Logging estruturado e consistente em todo o backend
- Tratamento explícito dos três pontos cegos de erros: câmera, FFmpeg e scheduler
- Handler global de exceções não tratadas no FastAPI
- Arquivo de log rotativo em disco (`logs/app.log`)
- README do backend: instalação do zero, configuração e execução
- README do frontend: instalação do zero, configuração e execução
- README raiz: visão geral do produto, arquitetura e como rodar tudo junto

### O Que Esta Fase NÃO Entrega
- Logs no frontend
- Sistema de monitoramento externo (Sentry, Datadog, etc.)
- Testes automatizados
- CI/CD
- Deploy em nuvem

### Pré-requisitos
- Fases 3 a 6 concluídas e funcionando
- Backend rodando sem erros em `http://localhost:8000`
- Frontend rodando sem erros em `http://localhost:5173`

---

## 🏗️ Arquitetura da Fase 7

```
backend/
├── logs/                         ← NOVO: diretório de logs (no .gitignore)
│   └── app.log                   ← criado automaticamente na primeira execução
└── app/
    ├── core/
    │   ├── logging_config.py     ← NOVO: configuração central de logging
    │   └── exceptions.py         ← MODIFICAR: handlers globais do FastAPI
    ├── infrastructure/
    │   └── camera/
    │       └── opencv_adapter.py ← MODIFICAR: logar erros da thread de captura
    └── main.py                   ← MODIFICAR: registrar logging + exception handlers

backend/README.md                 ← NOVO
frontend/README.md                ← NOVO
README.md                         ← NOVO (raiz do projeto, fora dos dois repositórios)
```

---

## 📋 Estado de Progresso

> **AGY:** Atualize os checkboxes conforme completar cada task.

- [x] **Task 7.1** — Logging: configuração central e formato consistente
- [x] **Task 7.2** — Polish: tratar pontos cegos de erro no backend
- [x] **Task 7.3** — Exception handlers globais no FastAPI
- [x] **Task 7.4** — README do backend (instalação do zero)
- [x] **Task 7.5** — README do frontend (instalação do zero)
- [x] **Task 7.6** — README raiz (visão geral + como rodar tudo junto)

---

## 🔗 Padrão de Log Definido

> **AGY:** Todo log gerado no projeto deve seguir este formato. Sem exceções.

### Formato
```
2024-01-15 10:30:45,123 | INFO     | app.camera.opencv_adapter | Câmera iniciada no device 0 (1280x720 @ 15fps)
2024-01-15 10:30:45,456 | ERROR    | app.infrastructure.camera | Falha ao ler frame: [Errno 5] Input/output error
2024-01-15 10:31:00,000 | INFO     | app.application.ttl       | TTL cleanup concluído em 0.42s: 3 vídeos removidos, 150.2 MB liberados
```

### Estrutura
```
{data} {hora} | {LEVEL:<8} | {module_path:<35} | {mensagem}
```

### Níveis por situação
```
DEBUG   → detalhes internos (frames capturados, paths de arquivo) — desligado em prod
INFO    → eventos normais do sistema (câmera iniciada, vídeo salvo, job concluído)
WARNING → situações anômalas mas recuperáveis (arquivo não encontrado, frame perdido)
ERROR   → falhas que precisam de atenção (FFmpeg falhou, câmera desconectada)
CRITICAL → falhas que comprometem o sistema inteiro (banco inacessível, disco cheio)
```

### Destinos
```
Console (stdout)  → nível INFO e acima (visível ao rodar o servidor)
Arquivo app.log   → nível DEBUG e acima (rastreamento completo)
Rotação           → 10MB por arquivo, manter últimos 5 arquivos
```

---

## ⚙️ Novas Configurações

> **AGY:** Adicionar ao `.env` e ao `app/config.py` antes de iniciar a Task 7.1.

```env
# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
```

```python
# Em app/config.py — adicionar à classe Settings:
log_level: str = "INFO"
log_dir: str = "./logs"
log_max_bytes: int = 10_485_760   # 10 MB
log_backup_count: int = 5
```

---

---

# TASK 7.1 — Logging: Configuração Central e Formato Consistente

## Objetivo
Criar a configuração central de logging que será aplicada a todo o backend. Um único ponto
de configuração garante formato consistente e evita que módulos individuais configurem
seus próprios handlers de forma inconsistente.

## Arquivos a Criar/Modificar

```
app/core/
└── logging_config.py    ← NOVO

app/main.py              ← MODIFICAR: chamar setup_logging() no início do lifespan
```

## Implementação

### `app/core/logging_config.py`

```python
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
```

### Modificar `app/main.py` — chamar `setup_logging()` no início

```python
# Adicionar import NO TOPO do arquivo, antes de qualquer outro import do projeto:
from app.core.logging_config import setup_logging

# setup_logging() deve ser a PRIMEIRA chamada dentro do lifespan,
# antes de create_all, scheduler.start(), ou qualquer outra coisa:
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()   # ← primeira linha do startup
    # ... resto do lifespan existente
```

> **NOTA PARA O AGY:** `setup_logging()` deve ser chamada ANTES de qualquer
> `import` que use `logging.getLogger(...)`. Em Python, se um módulo cria um logger
> antes do setup, ele não receberá os handlers configurados. A forma mais segura é
> chamar no início do lifespan, que é o ponto de entrada da aplicação.

### Substituir todos os `print()` por logging

> **AGY:** Varrer todos os arquivos do projeto e substituir qualquer `print()` por
> chamadas ao logger apropriado. Usar `get_logger(__name__)` em cada módulo.

```python
# Padrão a seguir em TODOS os módulos:
from app.core.logging_config import get_logger
logger = get_logger(__name__)

# Substituições:
print("Câmera iniciada")           → logger.info("Câmera iniciada")
print(f"Erro: {e}")                → logger.error(f"Erro: {e}", exc_info=True)
print("DEBUG: frame capturado")   → logger.debug("Frame capturado")
```

## Critérios de Aceitação da Task 7.1
- [ ] `uv run uvicorn app.main:app --reload` mostra logs no formato definido
- [ ] Arquivo `logs/app.log` é criado automaticamente na primeira execução
- [ ] Logs do uvicorn/access não poluem o console
- [ ] Logs do APScheduler não poluem o console
- [ ] Nenhum `print()` em nenhum arquivo do backend
- [ ] `get_logger(__name__)` usado em todos os módulos que já tinham `logging.getLogger`
- [ ] `logs/` está no `.gitignore`

---

---

# TASK 7.2 — Polish: Tratar Pontos Cegos de Erro no Backend

## Objetivo
Identificar e corrigir os três pontos cegos do projeto onde erros acontecem em threads
ou processos separados e podem passar completamente despercebidos. Esses pontos são:

1. **Thread de captura da câmera** — erros em `_capture_loop()` morrem silenciosamente
2. **Processo FFmpeg** — `stderr` do subprocess pode conter avisos críticos ignorados
3. **Job do scheduler** — exceções no `_run_ttl_job()` podem desativar futuras execuções

## Arquivos a Modificar

```
app/infrastructure/camera/opencv_adapter.py    ← MODIFICAR
app/infrastructure/video/ffmpeg_writer.py      ← MODIFICAR
app/infrastructure/scheduler/apscheduler.py   ← MODIFICAR
```

## Implementação

### Ponto Cego 1: Thread de Captura da Câmera

**Problema atual:** Se `_capture_loop()` encontrar um erro não tratado (ex: câmera
desconectada abruptamente, memória insuficiente), a thread simplesmente termina sem
nenhuma notificação. O `is_running` continua `True` mas nenhum frame é capturado.
O usuário vê o preview travado sem saber o motivo.

**Modificar `app/infrastructure/camera/opencv_adapter.py`:**

```python
# Modificar o método _capture_loop completo:
def _capture_loop(self) -> None:
    """
    Loop de captura rodando em thread separada.
    Captura frames continuamente e atualiza _latest_frame e _buffer.
    Todos os erros são logados e refletidos no status da câmera.
    A thread nunca termina silenciosamente.
    """
    logger.info(f"Thread de captura iniciada (device={self._device_index})")
    interval = 1.0 / settings.camera_fps
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 10

    while self._is_running:
        start = time.monotonic()

        try:
            if not self._cap or not self._cap.isOpened():
                raise RuntimeError("Câmera desconectada durante captura")

            ret, raw_frame = self._cap.read()

            if not ret:
                consecutive_errors += 1
                logger.warning(
                    f"Falha ao ler frame (tentativa {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})"
                )
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    raise RuntimeError(
                        f"Câmera falhou {MAX_CONSECUTIVE_ERRORS} vezes consecutivas"
                    )
                time.sleep(interval)
                continue

            # Frame lido com sucesso — resetar contador de erros
            consecutive_errors = 0

            encode_params = [cv2.IMWRITE_JPEG_QUALITY, settings.camera_jpeg_quality]
            success, buffer = cv2.imencode(".jpg", raw_frame, encode_params)

            if not success:
                logger.warning("Falha ao encodar frame como JPEG — frame descartado")
                continue

            frame = Frame(
                data=buffer.tobytes(),
                width=raw_frame.shape[1],
                height=raw_frame.shape[0],
                timestamp=time.time(),
            )

            with self._lock:
                self._latest_frame = frame
                self._buffer.append(frame)

        except Exception as e:
            # Captura qualquer erro não previsto — loga e encerra a thread com segurança
            error_msg = f"Erro crítico na thread de captura: {e}"
            logger.error(error_msg, exc_info=True)
            with self._lock:
                self._error = error_msg
            self._is_running = False
            break

        # Controle de FPS
        elapsed = time.monotonic() - start
        sleep_time = interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    logger.info("Thread de captura encerrada")
```

### Ponto Cego 2: Processo FFmpeg

**Problema atual:** O FFmpeg pode completar com código 0 mas emitir warnings críticos
no `stderr` que indicam problemas de qualidade ou compatibilidade. Além disso, o `stderr`
completo de uma falha hoje é truncado na mensagem de erro.

**Modificar `app/infrastructure/video/ffmpeg_writer.py`:**

```python
# Modificar o método _run_ffmpeg:
def _run_ffmpeg(
    self,
    temp_dir: str,
    output_path: str,
    fps: float,
    frame_count: int,
) -> float:
    """
    Executa FFmpeg para encodar frames JPEG em MP4.
    Loga stderr mesmo em caso de sucesso (pode conter warnings úteis).
    Retorna duração calculada em segundos.
    """
    input_pattern = os.path.join(temp_dir, "frame_%06d.jpg")

    cmd = [
        settings.ffmpeg_path,
        "-y",
        "-framerate", str(fps),
        "-i", input_pattern,
        "-c:v", "libx264",
        "-crf", str(settings.ffmpeg_crf),
        "-preset", settings.ffmpeg_preset,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    logger.debug(f"FFmpeg comando: {' '.join(cmd)}")
    logger.info(f"FFmpeg iniciado: {frame_count} frames @ {fps:.1f}fps → {output_path}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Logar stderr do FFmpeg independente do resultado
    # FFmpeg escreve tudo no stderr — mesmo em execuções bem-sucedidas
    if result.stderr:
        # Filtrar apenas as últimas linhas relevantes (FFmpeg é verboso)
        stderr_lines = result.stderr.strip().splitlines()
        relevant = [l for l in stderr_lines if any(
            kw in l.lower() for kw in ["error", "warning", "invalid", "failed", "unable"]
        )]
        if relevant:
            logger.warning(f"FFmpeg avisos: {'; '.join(relevant[-3:])}")
        else:
            logger.debug(f"FFmpeg stderr (últimas 3 linhas): {'; '.join(stderr_lines[-3:])}")

    if result.returncode != 0:
        # Logar stderr completo em caso de falha para diagnóstico
        logger.error(
            f"FFmpeg falhou (código {result.returncode}):\n{result.stderr[-2000:]}"
        )
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )

    # Verificar que o arquivo foi criado e tem tamanho > 0
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise VideoWriteError(
            f"FFmpeg completou mas arquivo não foi criado: {output_path}"
        )

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    duration = frame_count / fps
    logger.info(
        f"FFmpeg concluído: {duration:.1f}s de vídeo, {file_size_mb:.1f} MB, "
        f"arquivo: {os.path.basename(output_path)}"
    )

    return duration
```

### Ponto Cego 3: Job do Scheduler

**Problema atual:** Se `_run_ttl_job()` lançar uma exceção não capturada, o APScheduler
marca o job como falhado e pode deixar de agendá-lo nas próximas execuções, dependendo
da configuração. Isso mata silenciosamente o TTL automático.

**Modificar `app/infrastructure/scheduler/apscheduler.py`:**

```python
# Modificar _run_ttl_job completo:
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
```

## Critérios de Aceitação da Task 7.2

### Câmera
- [ ] Desconectar a webcam durante captura → log `ERROR` aparece em `logs/app.log`
- [ ] `GET /camera/status` retorna `is_running: false` e `error` preenchido após desconexão
- [ ] Thread não termina silenciosamente — log `"Thread de captura encerrada"` sempre aparece
- [ ] 10 frames consecutivos perdidos → câmera para com log claro

### FFmpeg
- [ ] Salvar momento → log `INFO` com duração e tamanho do arquivo
- [ ] Forçar falha (caminho inválido) → log `ERROR` com stderr completo
- [ ] Arquivo criado com tamanho 0 → `VideoWriteError` com mensagem clara

### Scheduler
- [ ] `POST /admin/ttl/run` → log `INFO` com resultado da limpeza
- [ ] Scheduler nunca para de agendar mesmo se o use case lançar exceção
- [ ] Log `WARNING` quando há erros não-fatais no CleanupResult

---

---

# TASK 7.3 — Exception Handlers Globais no FastAPI

## Objetivo
Adicionar handlers globais para capturar exceções não tratadas que chegam ao FastAPI.
Sem isso, erros internos retornam stack traces ao cliente (vazamento de informação)
e não são logados de forma rastreável.

## Arquivos a Modificar

```
app/core/exceptions.py    ← MODIFICAR
app/main.py               ← MODIFICAR: registrar handlers
```

## Implementação

### `app/core/exceptions.py` (substituir conteúdo)

```python
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registra todos os handlers globais de exceção na aplicação FastAPI.
    Chamar em main.py após criar a instância do app.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handler para HTTPExceptions explicitamente lançadas nas rotas (404, 401, etc).
        Loga como WARNING pois são erros esperados de uso da API.
        """
        logger.warning(
            f"HTTP {exc.status_code} | {request.method} {request.url.path} | {exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handler para erros de validação Pydantic (body inválido, params errados).
        Retorna os erros de forma estruturada sem stack trace.
        """
        errors = exc.errors()
        logger.warning(
            f"Validação falhou | {request.method} {request.url.path} | "
            f"{len(errors)} erro(s): {errors[0]['msg'] if errors else 'desconhecido'}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Dados inválidos na requisição",
                "errors": [
                    {
                        "field": " → ".join(str(loc) for loc in err["loc"]),
                        "message": err["msg"],
                    }
                    for err in errors
                ],
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handler de último recurso para exceções não tratadas.
        Loga como CRITICAL com stack trace completo.
        NUNCA retorna detalhes internos ao cliente (segurança).
        """
        logger.critical(
            f"Exceção não tratada | {request.method} {request.url.path} | "
            f"{type(exc).__name__}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno do servidor"},
        )
```

### Modificar `app/main.py` — registrar handlers

```python
# Adicionar import:
from app.core.exceptions import register_exception_handlers

# Chamar após criar a instância do app e ANTES de registrar os routers:
app = FastAPI(title="Sports Highlights API", version="0.1.0", lifespan=lifespan)

register_exception_handlers(app)  # ← adicionar aqui

# ... registrar routers
app.include_router(auth_router)
# etc.
```

## Critérios de Aceitação da Task 7.3
- [ ] `GET /rota-inexistente` retorna `{"detail": "Not Found"}` sem stack trace
- [ ] `POST /auth/login` com body inválido retorna 422 com campos e mensagens
- [ ] Simular exceção não tratada em uma rota → retorna 500 com `"Erro interno do servidor"`
- [ ] Stack trace da exceção não tratada aparece em `logs/app.log` como CRITICAL
- [ ] Stack trace NUNCA aparece no corpo da resposta HTTP
- [ ] Console mostra WARNING para 404 e 401, CRITICAL para 500

---

---

# TASK 7.4 — README do Backend

## Objetivo
Criar documentação de instalação do zero para o backend. O README deve ser seguido por
alguém que nunca viu o projeto antes, em uma máquina limpa, e conseguir rodar o servidor.

## Arquivo a Criar

```
sports-highlights-backend/README.md
```

## Conteúdo do README

O README deve conter exatamente as seguintes seções, nesta ordem:

### 1. Visão Geral
- O que é o projeto (2-3 linhas)
- O que este repositório contém (backend)
- Tecnologias principais: Python 3.11+, FastAPI, SQLite, OpenCV, FFmpeg

### 2. Pré-requisitos do Sistema
Instruções de instalação para cada dependência, separadas por sistema operacional
(macOS, Ubuntu/Debian, Windows):

```
- Python 3.11 ou superior
  macOS:   brew install python@3.11
  Ubuntu:  sudo apt install python3.11 python3.11-venv
  Windows: baixar em https://python.org/downloads (marcar "Add to PATH")

- uv (gerenciador de pacotes)
  Todos os SOs: curl -LsSf https://astral.sh/uv/install.sh | sh
  Windows:      powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

- FFmpeg
  macOS:   brew install ffmpeg
  Ubuntu:  sudo apt install ffmpeg
  Windows: https://ffmpeg.org/download.html → adicionar pasta bin ao PATH

- Webcam
  Qualquer webcam USB ou webcam integrada do notebook.
  Verificar que nenhum outro aplicativo está usando a câmera antes de iniciar.
```

### 3. Instalação
Passo a passo numerado:

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd sports-highlights-backend

# 2. Instalar dependências Python
uv sync

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações (ver seção Configuração abaixo)

# 4. Verificar FFmpeg
ffmpeg -version

# 5. Verificar câmera (opcional)
uv run python -c "import cv2; cap = cv2.VideoCapture(0); print('Câmera OK' if cap.isOpened() else 'Câmera NÃO encontrada'); cap.release()"
```

### 4. Configuração (`.env`)
Tabela com todas as variáveis, seus valores padrão e descrição:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| ADMIN_USERNAME | admin | Usuário de login |
| ADMIN_PASSWORD | changeme123 | Senha de login — **trocar antes de usar** |
| SECRET_KEY | — | Chave JWT — gerar com `python -c "import secrets; print(secrets.token_hex(32))"` |
| ALGORITHM | HS256 | Algoritmo JWT |
| ACCESS_TOKEN_EXPIRE_MINUTES | 480 | Expiração do token (8 horas) |
| DATABASE_URL | sqlite:///./sports_highlights.db | Banco de dados |
| VIDEOS_DIR | ./storage/videos | Onde os vídeos são salvos |
| TEMP_DIR | ./storage/temp | Arquivos temporários do FFmpeg |
| CAMERA_DEVICE_INDEX | 0 | Índice da câmera (0 = primeira câmera) |
| CAMERA_FPS | 15 | FPS de captura |
| CAMERA_WIDTH | 1280 | Largura da captura |
| CAMERA_HEIGHT | 720 | Altura da captura |
| BUFFER_DURATION_SECONDS | 120 | Duração do buffer circular (segundos) |
| TTL_DAYS | 7 | Dias até vídeos expirarem automaticamente |
| TTL_RUN_INTERVAL_HOURS | 1 | Frequência da limpeza automática |
| LOG_LEVEL | INFO | Nível de log (DEBUG, INFO, WARNING, ERROR) |
| FFMPEG_PATH | ffmpeg | Caminho do executável FFmpeg |

### 5. Executando o Servidor

```bash
# Desenvolvimento (com reload automático)
uv run uvicorn app.main:app --reload --port 8000

# O servidor estará disponível em:
# API:     http://localhost:8000
# Docs:    http://localhost:8000/docs
# Health:  http://localhost:8000/health
```

### 6. Verificando a Instalação
Sequência de comandos para confirmar que tudo funciona:

```bash
# 1. Health check
curl http://localhost:8000/health
# Esperado: {"status":"ok","version":"0.1.0"}

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme123"}'
# Esperado: {"access_token":"...","token_type":"bearer"}

# 3. Iniciar câmera (substituir TOKEN pelo token recebido acima)
curl -X POST http://localhost:8000/camera/start \
  -H "Authorization: Bearer TOKEN"
# Esperado: {"message":"Câmera iniciada com sucesso"}
```

### 7. Estrutura de Pastas
Descrição resumida de cada pasta e seu propósito.

### 8. Arquitetura
Diagrama ASCII das camadas (domain → application → infrastructure → routers)
com uma linha de descrição para cada camada.

### 9. Solução de Problemas

| Problema | Solução |
|----------|---------|
| `CameraNotFoundError: device index 0` | Testar índice 1: `CAMERA_DEVICE_INDEX=1` |
| `ffmpeg: command not found` | Verificar instalação e PATH do FFmpeg |
| `uv: command not found` | Reinstalar uv e reiniciar o terminal |
| Porta 8000 ocupada | Usar `--port 8001` ou matar o processo na porta |
| Banco de dados bloqueado | Parar outras instâncias do servidor |
| Vídeo não aparece na galeria | Verificar logs em `logs/app.log` |

## Critérios de Aceitação da Task 7.4
- [ ] README existe em `sports-highlights-backend/README.md`
- [ ] Todas as 9 seções estão presentes
- [ ] Instruções de instalação cobrem macOS, Ubuntu e Windows
- [ ] Tabela de configuração cobre todas as variáveis do `.env.example`
- [ ] Comandos `curl` de verificação funcionam na prática
- [ ] Alguém sem conhecimento prévio do projeto consegue rodar o backend seguindo o README

---

---

# TASK 7.5 — README do Frontend

## Objetivo
Criar documentação de instalação do zero para o frontend.

## Arquivo a Criar

```
sports-highlights-frontend/README.md
```

## Conteúdo do README

### 1. Visão Geral
- O que é o frontend (SPA React)
- Que o backend deve estar rodando primeiro
- Tecnologias: React 18, TypeScript, Vite, TailwindCSS, shadcn/ui

### 2. Pré-requisitos do Sistema

```
- Node.js 20 LTS ou superior
  macOS:   brew install node@20
  Ubuntu:  https://github.com/nodesource/distributions
  Windows: https://nodejs.org/en/download

- npm (vem com Node.js)
  Verificar: npm --version
```

### 3. Instalação

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd sports-highlights-frontend

# 2. Instalar dependências
npm install

# 3. Configurar variáveis de ambiente
cp .env.example .env.local
# Editar .env.local se o backend não estiver em http://localhost:8000
```

### 4. Configuração (`.env.local`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| VITE_API_URL | http://localhost:8000 | URL do backend FastAPI |

### 5. Executando o Frontend

```bash
npm run dev
# Disponível em: http://localhost:5173
```

### 6. Credenciais de Acesso
```
Usuário: admin
Senha:   changeme123 (ou o valor configurado em ADMIN_PASSWORD no backend)
```

### 7. Verificando a Instalação
- Acessar `http://localhost:5173` → redireciona para `/login`
- Login com credenciais → redireciona para `/dashboard`
- Dashboard mostra preview da câmera após clicar "Iniciar Câmera"

### 8. Build de Produção

```bash
npm run build       # gera pasta dist/
npm run preview     # preview local do build
```

### 9. Estrutura de Pastas
Descrição resumida de `src/pages`, `src/components`, `src/services`, `src/hooks`.

## Critérios de Aceitação da Task 7.5
- [ ] README existe em `sports-highlights-frontend/README.md`
- [ ] Todas as seções estão presentes
- [ ] Instruções de instalação de Node.js cobrem os 3 SOs
- [ ] Alguém sem conhecimento prévio consegue rodar o frontend seguindo o README

---

---

# TASK 7.6 — README Raiz

## Objetivo
Criar o README principal do projeto, fora dos dois repositórios, que dá uma visão geral
do produto e instrui como rodar backend e frontend juntos. Este é o primeiro documento
que qualquer pessoa verá ao conhecer o projeto.

## Arquivo a Criar

```
README.md  (na pasta raiz, fora de backend/ e frontend/)
```

## Conteúdo do README

### 1. Nome e Descrição do Produto

```
# Sports Highlights

Sistema local para captura automática de momentos incríveis em quadras esportivas.
Instalado na quadra, permite que donos e jogadores salvem os últimos 2 minutos
de uma partida com um único clique — sem câmeras especiais, sem internet, sem nuvem.
```

### 2. Como Funciona (Fluxo do Usuário)
Descrição em 4 passos com ícones ou numeração:
```
1. 📷  Câmera ligada → sistema grava continuamente em buffer circular
2. ⚡  Jogada incrível → operador clica "Salvar Momento"
3. 🎬  Sistema processa os últimos 2 minutos automaticamente
4. 🎥  Vídeo disponível na galeria para assistir e gerenciar
```

### 3. Arquitetura do Projeto

```
sports-highlights/
├── sports-highlights-backend/   # API FastAPI + processamento de vídeo
│   ├── app/
│   │   ├── domain/              # Entidades e interfaces (sem dependências externas)
│   │   ├── application/         # Use cases e lógica de negócio
│   │   ├── infrastructure/      # OpenCV, FFmpeg, APScheduler
│   │   └── routers/             # Endpoints FastAPI
│   └── storage/                 # Vídeos e arquivos temporários (local)
│
└── sports-highlights-frontend/  # SPA React
    └── src/
        ├── pages/               # LoginPage, DashboardPage, GalleryPage
        ├── components/          # Componentes reutilizáveis
        ├── services/            # Chamadas à API
        └── hooks/               # Estado e lógica React
```

### 4. Stack Técnica
Tabela resumida:

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11, FastAPI, SQLite |
| Captura de Vídeo | OpenCV |
| Processamento | FFmpeg |
| Agendamento | APScheduler |
| Frontend | React 18, TypeScript, Vite |
| Estilo | TailwindCSS, shadcn/ui |

### 5. Início Rápido

```bash
# Terminal 1 — Backend
cd sports-highlights-backend
uv sync
cp .env.example .env   # editar conforme necessário
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd sports-highlights-frontend
npm install
cp .env.example .env.local
npm run dev

# Acessar: http://localhost:5173
# Login: admin / changeme123
```

### 6. Requisitos de Hardware
```
- Computador com Windows, macOS ou Linux
- Webcam USB ou integrada
- 4 GB de RAM (mínimo)
- 10 GB de espaço em disco (para vídeos)
- Sem necessidade de internet
```

### 7. Links para Documentação Detalhada
```
→ Backend: sports-highlights-backend/README.md
→ Frontend: sports-highlights-frontend/README.md
```

## Critérios de Aceitação da Task 7.6
- [ ] README raiz existe fora das pastas de backend e frontend
- [ ] Fluxo do usuário está claro em 4 passos
- [ ] Seção "Início Rápido" permite rodar o projeto em menos de 5 minutos
- [ ] Requisitos de hardware estão explícitos
- [ ] Links para READMEs específicos estão presentes e corretos

---

---

## 🧪 Critérios de Aceitação da Fase 7 Completa

Só considerar a Fase 7 concluída — e o MVP pronto — quando **todos** os itens abaixo
forem verdadeiros:

### Logging
- [x] `logs/app.log` é criado na primeira execução
- [x] Todos os eventos importantes geram log com nível correto
- [x] Nenhum `print()` em nenhum arquivo do backend
- [x] `logs/` está no `.gitignore`
- [x] Logs de bibliotecas externas não poluem o console

### Polish de Erros
- [x] Desconectar câmera durante captura → log ERROR + câmera para graciosamente
- [x] FFmpeg falha → log ERROR com stderr + VideoWriteError com mensagem clara
- [x] Job do scheduler lança exceção → log CRITICAL + scheduler continua agendando
- [x] Rota inexistente → 404 sem stack trace no body
- [x] Body inválido → 422 com campos e mensagens legíveis
- [x] Exceção não tratada → 500 + CRITICAL no log + sem detalhes internos no body

### Documentação
- [x] `sports-highlights-backend/README.md` existe e está completo
- [x] `sports-highlights-frontend/README.md` existe e está completo
- [x] `README.md` raiz existe e está completo
- [x] Seguindo apenas os READMEs, é possível instalar e rodar o projeto do zero

### MVP Completo — Checklist Final
- [x] Login funciona com credenciais do `.env`
- [x] Preview da câmera aparece no Dashboard
- [x] Botão "Salvar Momento" salva vídeo e confirma com feedback
- [x] Galeria lista vídeos com data, duração e expiração
- [x] Player abre em modal e reproduz o vídeo
- [x] Delete remove o vídeo da galeria
- [x] TTL automático limpa vídeos expirados e deletados
- [x] Logs rastreáveis em `logs/app.log`
- [x] Documentação de instalação do zero nos READMEs

---

## 🚨 Problemas Comuns e Soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| Logs não aparecem no console | `setup_logging()` chamado depois dos imports | Mover para primeira linha do lifespan |
| `logs/app.log` não é criado | Sem permissão de escrita | Verificar permissão da pasta do projeto |
| Handler de 500 não captura erros | Registrado após os routers | Registrar handlers ANTES dos routers |
| APScheduler loga em excesso | Nível não silenciado | Garantir `logging.getLogger("apscheduler").setLevel(WARNING)` |
| README com comandos que não funcionam | Diferença de OS | Testar cada comando em uma máquina limpa antes de finalizar |

---

## 📝 Notas Finais para o Desenvolvedor

### Por que logging e não print()?
`print()` vai sempre para stdout sem contexto. `logging` permite: filtrar por nível,
rotacionar arquivos, adicionar timestamp e nome do módulo automaticamente, e no futuro
integrar com serviços de monitoramento sem mudar o código. É a diferença entre um
software amador e um produto.

### Por que handler de exceção global e não try/catch em cada rota?
Cada rota ter seu próprio try/catch é duplicação de código e fácil de esquecer.
O handler global é uma rede de segurança que captura tudo que passou pelos handlers
específicos. As duas abordagens se complementam — handlers específicos para erros
esperados, handler global para o inesperado.

### Por que o README de instalação cobre 3 sistemas operacionais?
Porque você não sabe em qual máquina vai instalar o produto na quadra do cliente.
Um README que funciona apenas no seu Mac é um README incompleto. Cobrir os 3 SOs
é o mínimo para um produto que será instalado por outra pessoa.

