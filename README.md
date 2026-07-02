# Sports Highlights

Sistema local para captura automática e gestão de momentos esportivos em quadras.
Permite gravar continuamente partidas usando uma webcam convencional instalada localmente e, com um único clique, processar e salvar os últimos 120 segundos da partida como arquivo MP4, tudo de forma local-first (sem nuvem, sem internet).

---

## 🗺️ Como Funciona (Fluxo do Usuário)

1. 📷 **Câmera Ativa:** O sistema captura continuamente o feed da câmera e armazena os frames em um buffer circular em memória.
2. ⚡ **Jogada Incrível:** Quando um momento marcante acontece, o operador clica no botão **"Salvar Momento"**.
3. 🎬 **Processamento:** O backend extrai os últimos 120 segundos do buffer e aciona o FFmpeg em background para gerar o arquivo MP4.
4. 🎥 **Galeria:** O vídeo final fica disponível instantaneamente na galeria local para visualização (via player modal) ou deleção.

---

## 🏗️ Arquitetura do Projeto

O projeto segue os princípios da **Clean Architecture**, mantendo as regras de negócio desacopladas das tecnologias de infraestrutura e interfaces de entrega:

```
sports-highlights/
├── app/                         # Backend (API FastAPI + Processamento de Vídeo)
│   ├── domain/                  # Camada mais interna (Entidades puras e interfaces dos adaptadores)
│   │   └── camera/              # Entidades Frame, CaptureSession, CleanupResult e interfaces
│   ├── application/             # Lógica de negócio / Casos de uso (Câmera, Gravação, TTL)
│   │   ├── camera/              # Casos de uso de câmera e gravação
│   │   └── ttl/                 # Caso de uso de limpeza automática de expirados
│   ├── infrastructure/          # Detalhes de tecnologia (implementação dos adaptadores)
│   │   ├── camera/              # OpenCVCameraAdapter (captura em thread daemon e buffer circular)
│   │   ├── video/               # FFmpegWriter (processamento do buffer para MP4)
│   │   └── scheduler/           # APScheduler (disparo de limpeza automática periódica)
│   ├── core/                    # Configurações globais, segurança e handlers de exceção
│   ├── database.py              # Configuração do banco SQLite e SQLAlchemy engine
│   └── main.py                  # Ponto de entrada da aplicação e ciclo de vida
│
└── sports-highlights-frontend/  # Frontend (Single Page Application React + Vite + TypeScript)
    └── src/
        ├── pages/               # LoginPage, DashboardPage, GalleryPage
        ├── components/          # AppLayout, ProtectedRoute e componentes de galeria
        ├── services/            # Chamadas e integrações com o backend (Fetch API)
        └── hooks/               # Estado compartilhado e lógica customizada (useApi, useVideos)
```

### Regras de Dependência de Camadas
- `domain` → Não importa nada do projeto (isolado e puro).
- `application` → Depende apenas de `domain`.
- `infrastructure` → Implementa contratos do `domain` e integra ferramentas externas (OpenCV, FFmpeg).
- `routers` → Consome apenas a camada de `application`.

---

## 🛠️ Stack Técnica

| Camada | Tecnologia | Propósito |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+ / FastAPI | Servidor API REST rápido e assíncrono |
| **Banco de dados** | SQLite / SQLAlchemy | Armazenamento de metadados dos vídeos locais |
| **Captura** | OpenCV (`opencv-python-headless`) | Captura de frames da webcam |
| **Processamento** | FFmpeg (Subprocess) | Encoding dos frames de memória para arquivo MP4 H.264 |
| **Agendamento** | APScheduler | Job periódico de limpeza de arquivos expirados |
| **Frontend** | React 18 / TypeScript / Vite | Rápido tempo de resposta e interface responsiva |
| **Estilos** | TailwindCSS / shadcn/ui | Interface com rica estética escura |

---

## 💻 Requisitos de Hardware

- **Sistema Operacional:** Windows 10/11, macOS ou Linux (Ubuntu/Debian)
- **Câmera:** Qualquer webcam USB ou webcam integrada do notebook
- **RAM:** Mínimo de 4 GB RAM
- **Disco:** Mínimo de 10 GB de espaço livre em disco (dedicado aos vídeos salvos)
- **Internet:** Não é necessária (tudo roda e é processado localmente em `localhost`)

---

## 🔌 Pré-requisitos do Sistema

Instale as dependências externas conforme seu sistema operacional:

### 1. Python 3.11+
- **macOS:** `brew install python@3.11`
- **Ubuntu/Debian:** `sudo apt install python3.11 python3.11-venv`
- **Windows:** Baixe em [python.org/downloads](https://www.python.org/downloads) (marque a opção "Add to PATH").

### 2. uv (Gerenciador de pacotes)
- **macOS/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows:** `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### 3. FFmpeg (Necessário no PATH do sistema)
- **macOS:** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **Windows:** Baixe em [ffmpeg.org/download.html](https://ffmpeg.org/download.html) e adicione a pasta `bin` às Variáveis de Ambiente do Sistema (PATH).

---

## 🚀 Instalação e Configuração

Siga os passos abaixo para configurar e rodar o backend local:

### 1. Preparando o Ambiente
```bash
# 1. Instalar as dependências e criar o ambiente virtual
uv sync --all-extras

# 2. Copiar as configurações de ambiente
cp .env.example .env

# 3. Gerar a chave secreta do JWT e colar no campo SECRET_KEY do .env
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Configurando o Arquivo `.env`

Abra o arquivo `.env` gerado e ajuste as configurações se necessário:

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `ADMIN_USERNAME` | `admin` | Usuário do operador do sistema |
| `ADMIN_PASSWORD` | `admin` | Senha fixa de acesso — **troque em produção** |
| `SECRET_KEY` | `—` | Chave usada para assinar os tokens JWT |
| `ALGORITHM` | `HS256` | Algoritmo de criptografia do token |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Duração do login do operador (8 horas) |
| `DATABASE_URL` | `sqlite:///./sports_highlights.db` | Caminho do arquivo SQLite local |
| `VIDEOS_DIR` | `./storage/videos` | Diretório onde os arquivos MP4 finais são salvos |
| `TEMP_DIR` | `./storage/temp` | Diretório temporário dos frames para o FFmpeg |
| `CAMERA_DEVICE_INDEX` | `0` | Índice da webcam no sistema (geralmente 0) |
| `CAMERA_FPS` | `15` | Taxa de quadros por segundo para gravação |
| `CAMERA_WIDTH` | `1280` | Resolução horizontal da câmera |
| `CAMERA_HEIGHT` | `720` | Resolução vertical da câmera |
| `CAMERA_JPEG_QUALITY` | `70` | Qualidade de compressão JPEG em memória (1-100) |
| `BUFFER_DURATION_SECONDS` | `120` | Duração do vídeo gerado no buffer circular (segundos) |
| `BUFFER_MAX_FRAMES` | `1800` | Limite máximo de frames no buffer (CAMERA_FPS * BUFFER_DURATION) |
| `TTL_DAYS` | `7` | Duração (em dias) que os vídeos são mantidos antes do TTL apagar |
| `TTL_RUN_INTERVAL_HOURS` | `1` | Intervalo de execução do job de limpeza (APScheduler) |
| `TTL_TEMP_MAX_AGE_HOURS` | `24` | Tempo limite para remoção de lixo temporário órfão |
| `LOG_LEVEL` | `INFO` | Nível mínimo de logs exibido (DEBUG, INFO, WARNING, ERROR) |

### 3. Executando o Servidor

```bash
# Iniciar o servidor local (FastAPI rodando com reload ativo)
uv run uvicorn app.main:app --reload --port 8000
```
- A API estará disponível em: [http://localhost:8000](http://localhost:8000)
- Documentação interativa (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- Logs persistidos e rotativos gravados em: `./logs/app.log`

---

## 🧪 Verificando a Instalação

Para validar que o backend está funcionando e aceitando conexões locais, execute em outro terminal:

```bash
# 1. Health check público
curl http://localhost:8000/health
# Retorno esperado: {"status":"ok","version":"0.1.0"}

# 2. Login administrativo
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
# Retorno esperado: {"access_token":"TOKEN_LONGO","token_type":"bearer"}

# 3. Status da câmera (substitua TOKEN pelo retornado no passo 2)
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/camera/status
# Retorno esperado: {"is_running":false,"device_index":0,"fps":0.0,"resolution":[0,0],"error":null,"is_healthy":false}
```

---

## 🚨 Solução de Problemas

| Problema | Causa | Solução |
| :--- | :--- | :--- |
| `CameraNotFoundError` no index 0 | Câmera sendo usada por outro app ou sem permissão | Feche outros aplicativos de câmera. Se tiver mais de uma webcam conectada, tente alterar `CAMERA_DEVICE_INDEX=1` ou `2` no `.env`. |
| `ffmpeg: command not found` | FFmpeg não instalado ou ausente do PATH | Siga o passo 3 de Pré-requisitos correspondente ao seu sistema operacional. Certifique-se de reabrir o terminal após a instalação. |
| O vídeo travou ou parou de transmitir | Perda excessiva de frames na thread de captura | Verifique o status da câmera via `GET /camera/status` ou analise a pilha de erros detalhada no arquivo de log local `./logs/app.log`. |
| Banco de dados travado | SQLite bloqueado por outra instância ativa | Certifique-se de que não há outro processo uvicorn rodando no background na mesma porta e pasta. |
