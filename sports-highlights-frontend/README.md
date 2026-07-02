# Sports Highlights Frontend

Interface web interativa desenvolvida em React para controle, monitoramento em tempo real e visualização de momentos esportivos gerados pelo backend do **Sports Highlights**.

---

## 🗺️ Visão Geral

Este repositório contém a Single Page Application (SPA) que se comunica com o servidor de backend local. Ela fornece:
- **Painel Administrativo:** Status de conexão com a API e status operacional da câmera local.
- **Preview de Vídeo ao Vivo:** Visualização de baixa latência em MJPEG diretamente do feed de gravação.
- **Gravação sob Demanda:** Botão para capturar retroativamente os últimos 120 segundos de partida.
- **Galeria e Player Modal:** Visualização de todos os momentos salvos com player HTML5 nativo e opção de deleção rápida (soft delete).

---

## 🔌 Pré-requisitos do Sistema

Para rodar a interface do frontend, você precisa ter:

### 1. Node.js (Versão 20 LTS ou superior)
- **macOS:** `brew install node@20`
- **Ubuntu/Debian:** Siga as instruções do Nodesource: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs`
- **Windows:** Baixe o instalador `.msi` LTS em [nodejs.org](https://nodejs.org).

### 2. npm (Normalmente já vem instalado junto com o Node.js)
- Verifique a versão rodando: `npm --version`

---

## 🚀 Instalação e Configuração

### 1. Instalar as dependências do npm
```bash
# Navegar até o diretório do frontend
cd sports-highlights-frontend

# Instalar pacotes necessários
npm install
```

### 2. Configurar variáveis de ambiente
```bash
# Copiar o arquivo de exemplo
cp .env.example .env.local
```
Abra o arquivo `.env.local` e confirme se a URL da API corresponde ao seu servidor de backend:

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://localhost:8000` | URL do servidor de backend FastAPI ativo |

---

## 💻 Executando em Desenvolvimento

Garanta que o servidor backend esteja ativo em `http://localhost:8000` e então execute:

```bash
# Iniciar o servidor dev de desenvolvimento do Vite
npm run dev
```
O frontend estará acessível em: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Credenciais de Acesso Fixas (MVP)

A autenticação é realizada usando credenciais administrativas definidas no `.env` do backend:
- **Usuário:** `admin`
- **Senha:** `admin` (ou o valor configurado em `ADMIN_PASSWORD` no backend)

O token JWT recebido no login é armazenado **estritamente em memória** para maior segurança.

---

## 🧪 Verificando a Instalação

1. Abra seu navegador em [http://localhost:5173](http://localhost:5173).
2. Você deverá ser redirecionado automaticamente para a página de **Login**.
3. Insira as credenciais do operador e clique em **Entrar**.
4. Ao efetuar o login, você será redirecionado para o **Dashboard**.
5. No Dashboard, você poderá clicar em **"Iniciar Câmera"** para receber o preview ao vivo da câmera e, em seguida, clicar em **"Salvar Momento"** para iniciar um job de gravação.

---

## 📦 Build de Produção

Para gerar e validar os arquivos compilados otimizados para produção:

```bash
# 1. Executar a compilação do TypeScript e o bundler Vite
npm run build

# 2. Iniciar um servidor local estático para testar o bundle de produção gerado
npm run preview
```
O build estático e otimizado é gerado no diretório `./dist/`.

---

## 📁 Estrutura de Pastas

Principais pastas da base de código do frontend:

- `src/components/`: Componentes visuais atômicos estruturados de UI (tabelas, cards, dialogs) e layouts reutilizáveis.
- `src/components/ui/`: Biblioteca básica de elementos gerada pelo shadcn/ui (inputs, cards, alerts).
- `src/hooks/`: Hooks React customizados para consumo de APIs e polling de status em tempo real (`useCameraStatus`, `useSaveMoment`).
- `src/pages/`: Páginas da aplicação (`LoginPage`, `DashboardPage`, `GalleryPage`).
- `src/services/`: Camada de chamadas AJAX de API (`cameraService`, `momentsService`, `videoService`).
- `src/lib/`: Instância central do cliente HTTP (`apiFetch`) e mapeamento das rotas internas.
- `src/contexts/`: Contextos globais (ex: AuthContext para controle de sessões e login em memória).
