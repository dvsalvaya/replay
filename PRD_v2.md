# PRD — Sports Highlights
## Versão 2.0 | Revisado após implementação das Fases 3–7

> **Histórico de versões**
> v1.0 — Documento inicial (pré-desenvolvimento)
> v2.0 — Revisado para refletir decisões tomadas durante o desenvolvimento do MVP

---

## 01 — Visão do Produto

### Problema
Jogadores de quadras esportivas pagas não conseguem registrar seus melhores momentos
de forma simples e automática. Câmeras manuais exigem operador dedicado, e soluções
profissionais são inacessíveis financeiramente para donos de quadras pequenas.

### Solução
Software instalado localmente na quadra que mantém um buffer contínuo de vídeo.
Com um único clique, o operador salva os últimos 2 minutos automaticamente —
sem configuração, sem internet, sem câmera especial.

### Diferencial Competitivo
- Único produto com esse foco no mercado local
- Instalação simples em qualquer notebook com webcam
- Alto valor percebido pelo dono da quadra (aumenta engajamento dos jogadores)
- Funciona 100% offline — sem dependência de internet ou nuvem

### Visão de Longo Prazo
MVP local-first → validação com 3 clientes → busca de investimento →
migração para cloud → compartilhamento externo → multi-câmera → analytics

---

## 02 — Público-Alvo

### Usuário Primário
**Dono ou operador de quadra esportiva** (futebol de salão, grama sintética, vôlei, etc.)
- Acessa o sistema via browser no notebook da quadra
- Monitora a partida pelo preview ao vivo
- Clica "Salvar Momento" quando ocorre uma jogada especial
- Gerencia os vídeos salvos pela galeria

### Mercado Inicial
- Meta do MVP: 3 clientes (quadras individuais)
- Uso previsível: 1 quadra por instalação, 1 usuário simultâneo
- Sem picos de tráfego — fluxo contínuo e constante durante o horário de funcionamento

---

## 03 — Escopo do MVP

### ✅ Dentro do Escopo

| Funcionalidade | Descrição |
|----------------|-----------|
| Autenticação | Login com usuário e senha fixos via `.env` |
| Preview ao vivo | Stream MJPEG da webcam no browser |
| Buffer circular | Últimos 120 segundos mantidos em memória continuamente |
| Salvar Momento | Botão que processa o buffer e salva como MP4 |
| Galeria | Lista de vídeos salvos com nome, data e duração |
| Player | Reprodução em modal com player HTML5 nativo |
| Delete manual | Remoção de vídeo pelo operador (soft delete) |
| TTL automático | Vídeos expiram após 7 dias e são limpos automaticamente |
| Logs | Registro de eventos e erros em arquivo rotativo |
| Documentação | README de instalação do zero para os 3 principais SOs |

### ❌ Fora do Escopo (MVP)

| Funcionalidade | Decisão |
|----------------|---------|
| Corte de vídeo | **Removido permanentemente.** O buffer circular já resolve o problema — o operador clica no momento certo e os 2 minutos anteriores são salvos. Edição posterior é desnecessária. |
| Compartilhamento externo | **Pós-MVP.** Link público com expiração, via upload para nuvem. |
| Multi-câmera | **Pós-MVP.** MVP suporta apenas 1 câmera por instalação. |
| Analytics | **Pós-MVP.** Visualizações, jogadores mais salvos, etc. |
| Cadastro de clientes | **Pós-MVP.** Credenciais fixas no MVP. |
| App mobile | **Pós-MVP.** Apenas browser desktop no MVP. |
| Upload para nuvem | **Pós-MVP.** Armazenamento 100% local no MVP. |
| Pagamentos / assinatura | **Pós-MVP.** Cobrança será implementada após validação. |
| Múltiplas quadras | **Pós-MVP.** Uma instalação por quadra no MVP. |
| IA / detecção automática | **Fora de escopo.** Não planejado. |

---

## 04 — Histórias de Usuário

### Como dono/operador de quadra...

**Autenticação**
> Quero fazer login com usuário e senha para acessar o sistema com segurança.

**Monitoramento**
> Quero ver o feed ao vivo da câmera para monitorar a partida em andamento.
> Quero saber se a câmera está funcionando (status visível no dashboard).

**Captura**
> Quero clicar em "Salvar Momento" e ter os últimos 2 minutos salvos automaticamente.
> Quero ver feedback imediato de que o salvamento foi iniciado.
> Quero ser avisado quando o vídeo estiver pronto na galeria.

**Galeria**
> Quero ver todos os momentos salvos em uma lista ordenada por data.
> Quero saber quanto tempo falta para cada vídeo expirar.
> Quero assistir qualquer vídeo sem sair da galeria.
> Quero deletar vídeos que não quero mais manter.

**Manutenção**
> Quero que vídeos antigos sejam removidos automaticamente para não lotar o disco.
> Quero que o sistema continue funcionando mesmo se houver um erro pontual.

---

## 05 — Funcionalidades Detalhadas

### F1 — Autenticação
- `POST /auth/login` com `username` e `password`
- Credenciais fixas carregadas do `.env` (sem banco de usuários)
- Retorna JWT com expiração de 480 minutos (8 horas)
- Todas as rotas da API exigem token Bearer (exceto `/health` e `/auth/login`)
- Token armazenado em memória no frontend (nunca em `localStorage`)
- **Sem cadastro de novos usuários no MVP**

### F2 — Preview ao Vivo (MJPEG Stream)
- Webcam capturada continuamente via OpenCV em thread daemon separada
- Stream MJPEG servido em `GET /camera/stream?token=<jwt>`
- Frontend exibe preview com tag `<img src>` nativa — sem WebSocket
- FPS configurável via `.env` (padrão: 15 FPS)
- Resolução configurável (padrão: 1280×720)
- Status da câmera disponível em `GET /camera/status`
- Controles: `POST /camera/start` e `POST /camera/stop`
- **Latência aceitável: até 2 segundos no MVP**

### F3 — Buffer Circular
- `collections.deque` com `maxlen` configurável (padrão: 1800 frames = 120s @ 15fps)
- Alimentado a cada frame capturado pela thread de câmera
- Thread-safe via `threading.Lock`
- Snapshot atômico ao salvar (cópia dos frames sob o lock)
- Limpeza automática ao parar a câmera
- **Uso de memória estimado: ~80-150 MB para 120 segundos**

### F4 — Salvar Momento
- `POST /moments/save` com `title` opcional
- Verifica câmera ativa e buffer não-vazio antes de processar
- Retorna `job_id` imediatamente (processamento em `BackgroundTasks`)
- FFmpeg converte frames JPEG → MP4 com H.264 + `yuv420p` + `faststart`
- Metadados salvos no SQLite: `filename`, `duration_seconds`, `file_size_bytes`, `expires_at`
- Status do job via `GET /moments/jobs/{job_id}` (polling a cada 1.5s no frontend)
- **Tempo esperado de processamento: menos de 30 segundos para 120s de vídeo**

### F5 — Galeria e Player
- `GET /videos` retorna lista paginada, ordenada por `created_at DESC`
- Filtro automático: apenas vídeos com `is_deleted=False` e `expires_at > now()`
- Cada item exibe: nome, data, duração, tamanho e dias restantes para expiração
- Badge âmbar quando `days_until_expiry <= 2`
- Clique no vídeo abre modal com player HTML5 nativo
- Player suporta seeking via header `Accept-Ranges: bytes`
- Fechar modal para o vídeo e limpa o `src`
- `DELETE /videos/{id}` faz soft delete (marca `is_deleted=True`, não apaga arquivo)
- **Sem paginação visível no frontend no MVP — lista completa de uma vez**

### F6 — TTL Automático
- Job periódico via APScheduler (padrão: a cada 1 hora)
- Candidatos: `expires_at < now()` OU `is_deleted=True`
- Para cada candidato: apaga arquivo físico + remove registro do banco (hard delete)
- Limpa arquivos órfãos em `storage/temp/` com mais de 24 horas
- Erros não-fatais são logados mas não interrompem o job
- `GET /admin/ttl/status` — status do scheduler e resultado da última execução
- `POST /admin/ttl/run` — execução manual para testes
- **TTL padrão: 7 dias (configurável via `.env`)**

### F7 — Logs e Resiliência
- Logging centralizado com formato consistente: `data | LEVEL | módulo | mensagem`
- Console: INFO e acima
- Arquivo rotativo `logs/app.log`: DEBUG e acima, 10MB por arquivo, 5 arquivos
- Tratamento explícito dos três pontos cegos: thread de câmera, FFmpeg, scheduler
- Handler global de exceções não tratadas (500 sem stack trace no body)
- Erros de validação (422) com campos e mensagens legíveis
- **Nenhum `print()` no código — apenas `logging`**

---

## 06 — Requisitos Não Funcionais

| Requisito | Especificação |
|-----------|--------------|
| **Plataforma** | Windows, macOS e Linux com Python 3.11+ |
| **Conectividade** | 100% offline — sem dependência de internet |
| **Usuários simultâneos** | 1 (MVP com 1 quadra) |
| **Latência do preview** | ≤ 2 segundos |
| **Tempo de salvamento** | ≤ 30 segundos para 120s de vídeo |
| **Armazenamento** | Sistema de arquivos local + SQLite |
| **Segurança** | JWT, senhas comparadas com `secrets.compare_digest` |
| **Memória** | ~80-150 MB para buffer de 120s @ 15fps @ 720p |
| **Disponibilidade** | Sem SLA formal no MVP — sistema local |

---

## 07 — Stack Técnica

### Backend

| Componente | Tecnologia | Justificativa |
|-----------|-----------|---------------|
| Linguagem | Python 3.11+ | Ecossistema rico para vídeo e ML futuro |
| Framework | FastAPI | Async nativo, Swagger automático, tipagem forte |
| Banco de dados | SQLite + SQLAlchemy | Zero config, embedded, suficiente para 1 quadra |
| Captura de vídeo | OpenCV (`opencv-python-headless`) | Padrão da indústria, fácil de usar |
| Processamento | FFmpeg (subprocess) | Robusto, cross-platform, codec H.264 |
| Scheduler | APScheduler 3.x | Roda no processo FastAPI, sem infra extra |
| Auth | JWT (`python-jose`) | Stateless, simples, sem banco de sessões |
| Package manager | `uv` | Mais rápido que pip, lock file confiável |

### Frontend

| Componente | Tecnologia | Justificativa |
|-----------|-----------|---------------|
| Framework | React 18 + TypeScript | Componentes reativos, tipagem segura |
| Build | Vite | Setup mínimo, HMR rápido |
| Estilo | TailwindCSS | Utilitário, sem CSS customizado |
| Componentes | shadcn/ui | Cópia local dos componentes, controle total |
| Comunicação | Fetch nativo | Sem dependências extras no MVP |
| Estado auth | Context API | Simples, suficiente para 1 usuário |
| Roteamento | React Router v6 | Padrão, suporte a rotas protegidas |

### Arquitetura de Camadas (Clean Architecture)

```
┌─────────────────────────────────────────────────┐
│  DOMAIN (entidades + interfaces)                │
│  Não importa nada externo ao projeto            │
│  Frame, CameraStatus, VideoBuffer, SaveJob...   │
├─────────────────────────────────────────────────┤
│  APPLICATION (use cases)                        │
│  Importa apenas domain                          │
│  CameraUseCases, SaveMomentUseCase, TTLUseCase  │
├─────────────────────────────────────────────────┤
│  INFRASTRUCTURE (adaptadores externos)          │
│  Importa domain + libs externas                 │
│  OpenCVAdapter, FFmpegWriter, APScheduler       │
├─────────────────────────────────────────────────┤
│  INTERFACE (routers FastAPI)                    │
│  Importa application + schemas                  │
│  /auth, /camera, /moments, /videos, /admin      │
└─────────────────────────────────────────────────┘
```

**Regra fundamental:** camadas internas nunca conhecem camadas externas.
Se amanhã trocar OpenCV por outra lib, só a infrastructure muda.

---

## 08 — Estrutura de Repositórios

```
(pasta raiz)
├── README.md                          ← visão geral + início rápido
│
├── sports-highlights-backend/
│   ├── README.md                      ← instalação do zero do backend
│   ├── pyproject.toml                 ← gerenciado pelo uv
│   ├── .env.example
│   ├── logs/                          ← gerado automaticamente
│   ├── storage/
│   │   ├── videos/                    ← MP4 salvos
│   │   └── temp/                      ← temporários do FFmpeg
│   └── app/
│       ├── domain/camera/             ← entidades e interfaces
│       ├── application/camera/        ← use cases de câmera
│       ├── application/ttl/           ← use case de limpeza
│       ├── infrastructure/camera/     ← OpenCV adapter
│       ├── infrastructure/video/      ← FFmpeg writer
│       ├── infrastructure/scheduler/  ← APScheduler
│       ├── auth/                      ← router de autenticação
│       ├── camera/                    ← router de câmera
│       ├── moments/                   ← router de salvamento
│       ├── videos/                    ← router de galeria
│       ├── admin/                     ← router de administração
│       └── core/                      ← security, logging, exceptions
│
└── sports-highlights-frontend/
    ├── README.md                      ← instalação do zero do frontend
    ├── package.json
    ├── .env.example
    └── src/
        ├── pages/                     ← LoginPage, DashboardPage, GalleryPage
        ├── components/                ← layout/, gallery/, ui/ (shadcn)
        ├── services/                  ← authService, cameraService, videoService
        ├── hooks/                     ← useCameraStatus, useVideos, useSaveMoment
        ├── contexts/                  ← AuthContext
        └── lib/                       ← api.ts, utils.ts, routes.ts
```

---

## 09 — Roadmap de Implementação

| Fase | Conteúdo | Status |
|------|----------|--------|
| Prompt 01 | Backend: FastAPI + SQLite + JWT | ✅ Documentado |
| Prompt 02 | Frontend: React + Vite + shadcn/ui | ✅ Documentado |
| Fase 3 | Câmera ao vivo + stream MJPEG | ✅ Documentado |
| Fase 4 | Buffer circular + Salvar Momento | ✅ Documentado |
| Fase 5 | Galeria + Player + Delete | ✅ Documentado |
| Fase 6 | TTL automático + APScheduler | ✅ Documentado |
| Fase 7 | Polish backend + Logs + README | ✅ Documentado |

---

## 10 — Roadmap Pós-MVP

> Estas funcionalidades **não serão implementadas** antes da validação com 3 clientes
> e da busca por investimento.

| Funcionalidade | Descrição | Prioridade |
|----------------|-----------|-----------|
| **Compartilhamento externo** | Link público com expiração, upload para nuvem (S3 ou Cloudinary) | Alta |
| **Multi-câmera** | Suporte a múltiplas câmeras por quadra | Média |
| **App mobile** | Visualização dos momentos no celular dos jogadores | Média |
| **Analytics** | Visualizações por vídeo, horários de pico, tendências | Baixa |
| **Cadastro de clientes** | Múltiplos usuários por quadra com permissões | Alta |
| **Pagamentos** | Assinatura mensal via Stripe ou outro gateway | Alta |
| **Deploy em nuvem** | Backend na nuvem para acesso remoto | Alta |
| **Detecção automática** | IA para detectar gols/jogadas sem operador | Baixa |

---

## 11 — Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Câmera desconecta durante captura | Média | Alto | Thread daemon com retry + log de erro + status visível |
| Disco cheio por vídeos acumulados | Baixa | Alto | TTL automático + alerta de espaço (pós-MVP) |
| FFmpeg ausente na máquina do cliente | Alta | Alto | Verificação no startup + instrução clara no README |
| Performance ruim em hardware antigo | Média | Médio | FPS e resolução configuráveis, preset `ultrafast` |
| Buffer muito grande → OutOfMemory | Baixa | Alto | `maxlen` fixo no deque + configurável no `.env` |
| Token JWT expirado durante uso | Baixa | Baixo | Expiração longa (8h) + redirect para login |

---

## 12 — Decisões Técnicas Registradas

> Este registro existe para que o raciocínio por trás das decisões não se perca.

| Decisão | Alternativas Consideradas | Justificativa |
|---------|--------------------------|---------------|
| Local-first no MVP | Cloud desde o início | Elimina DevOps, custo zero, valida produto antes de infraestrutura |
| SQLite e não PostgreSQL | PostgreSQL, MySQL | Zero config, embedded, portátil; migração simples depois |
| MJPEG e não WebSocket | WebSocket, HLS | Funciona com `<img src>` nativo, sem JS extra, suficiente para 15fps |
| Token em memória e não localStorage | localStorage, cookie | Evita XSS, token some ao fechar a aba |
| BackgroundTasks e não threading | threading.Thread, Celery | Gerenciado pelo FastAPI, Session válida durante execução |
| APScheduler e não cron | Cron do OS, Celery Beat | Roda no processo Python, portátil entre SOs |
| Soft delete antes de hard delete | Hard delete imediato | Janela de segurança, arquivo pode estar em uso no player |
| FFmpeg via subprocess | OpenCV VideoWriter | Cross-platform, codec H.264 robusto, `yuv420p` para compatibilidade |
| Corte de vídeo removido | Slider, campos de texto | Buffer circular já resolve o problema — operador clica no momento certo |
| Clean Architecture | MVC, estrutura flat | Testabilidade, trocar OpenCV/FFmpeg sem tocar regras de negócio |
| `uv` e não pip/poetry | pip+venv, poetry | Mais rápido, lock file confiável, CLI moderna |

