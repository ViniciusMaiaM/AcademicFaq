# FAQ Acadêmico UFRN — RAG (WIP)

<p align="center">
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/langchain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
  <img src="https://img.shields.io/badge/docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white"/>
  <img src="https://img.shields.io/badge/ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black"/>
</p>

- [📖 Documentação](#-documentação)
- [📑 Sobre o projeto](#-sobre-o-projeto)
- [🧩 Componentes e responsabilidades](#-componentes-e-responsabilidades)
- [🔐 Autenticação](#-autenticação)
- [📦 Gerenciador de pacotes](#-gerenciador-de-pacotes)
- [📂 Estrutura do repositório](#-estrutura-do-repositório)
- [🚀 Começando](#-começando)
- [🧪 Testes](#-testes)
- [🎯 Funcionalidades](#-funcionalidades)
- [📊 Monitoramento](#-monitoramento)
- [❗ Solução de problemas](#-solução-de-problemas)
- [📌 Status (WIP)](#-status-wip)
- [💡 Melhorias futuras sugeridas](#-melhorias-futuras-sugeridas)

## 📖 Documentação

- Swagger (local, quando a API estiver rodando): http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## 📑 Sobre o projeto

FAQ Acadêmico é um chatbot que responde perguntas sobre documentos oficiais da UFRN (calendário universitário, regulamento de graduação, resoluções de TCC/estágio/atividades complementares) usando RAG (Retrieval-Augmented Generation) com a API da OpenAI. O foco é qualidade e confiabilidade da resposta — guardrail contra alucinação, extração de PDF ciente de estrutura, avaliação contra golden set — além de custo sob controle (cache exato + semântico, rate limiting) e autenticação restrita à comunidade UFRN.

## 🧩 Componentes e responsabilidades

- **backend** (Python + FastAPI)
    - API REST: `/ask` (pergunta ao RAG), `/auth` (cadastro/login), `/cache`, `/feedback`, `/metrics`.
    - RAG: retrieval MMR no ChromaDB + guardrail de groundedness + geração via OpenAI.
    - Persistência: SQLite (SQLAlchemy + Alembic), configurável para PostgreSQL via `DATABASE_URL`.
- **frontend** (Python + Streamlit)
    - Interface de chat, tela de login/cadastro, feedback 👍/👎, perguntas sugeridas por categoria.
- **scripts/ingest.py**
    - Carrega os PDFs de `docs/`, extrai texto (PyMuPDF), faz chunking ciente de estrutura (por artigo, nas resoluções) e popula o ChromaDB.
- **scripts/evaluate.py**
    - Roda o pipeline de RAG de verdade contra um golden set de perguntas com resposta conhecida (`evals/golden_set.json`) e calcula métricas de qualidade (retrieval recall, answer recall, taxa de fallback).

## 🔐 Autenticação

A API exige login em **todas as rotas de negócio** (`/ask`, `/cache`, `/feedback`, `/metrics`) — só a raiz (`/`) e as próprias rotas de autenticação (`/auth/register`, `/auth/login`) ficam abertas. Não tem sessão nem JWT: o cadastro/login devolve uma **API key simples**, que o cliente reenvia em todo request no header `X-API-Key`.

- **Cadastro exige e-mail institucional** — precisa conter `ufrn` no domínio (`@ufrn.br`, `@alunos.ufrn.br`, `@ceres.ufrn.br`, etc.). Não há verificação de titularidade do e-mail (não envia link de confirmação), só validação de formato/domínio.
- O login devolve a **mesma** API key gerada no cadastro (não expira, não é regenerada a cada login).
- Pela interface Streamlit, isso é transparente: a tela de login/cadastro aparece antes do chat, e a API key fica guardada só na sessão do navegador (`st.session_state`) — feche a aba e precisa logar de novo.

Testando via `curl`:
```bash
# Cadastro
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "seu.nome@alunos.ufrn.br", "password": "sua_senha_aqui"}'
# -> {"email": "...", "api_key": "..."}

# Usando a API key nas rotas protegidas
curl -X POST http://localhost:8000/api/v1/ask/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SUA_API_KEY_AQUI" \
  -d '{"question": "Quando começam as aulas?"}'
```

## 📦 Gerenciador de pacotes

- Python: pip + `requirements.txt` (backend/scripts) e `frontend/requirements.txt` (frontend — dependências mais leves, imagem Docker menor).

## 📂 Estrutura do repositório

```
academicfaq/
├── docs/                       # PDFs dos regulamentos acadêmicos (lidos pelo ingest)
├── evals/golden_set.json       # Perguntas com resposta conhecida, para scripts/evaluate.py
├── scripts/ingest.py           # Processa os documentos e popula o ChromaDB
├── scripts/evaluate.py         # Avalia a qualidade das respostas contra o golden set
├── backend/
│   ├── main.py                 # Entrypoint da API FastAPI
│   ├── services/rag.py         # Lógica do RAG (retrieval + guardrail)
│   ├── services/semantic_cache.py
│   ├── core/security.py        # Hash de senha, geração de API key, validação de e-mail @ufrn
│   ├── core/deps.py            # Dependency de autenticação (X-API-Key)
│   ├── api/routes/             # /ask, /auth, /cache, /feedback, /metrics
│   ├── alembic/                # Migrações do banco
│   ├── tests/                  # Suíte de testes (pytest)
│   └── Dockerfile
├── frontend/
│   ├── main.py                 # Entrypoint da interface Streamlit
│   ├── components/auth.py      # Telas de login/cadastro
│   ├── pages/                  # Páginas extras (multipage app) — ex.: Analytics
│   ├── tests/                  # Suíte de testes (pytest)
│   ├── requirements.txt        # Dependências de produção do frontend
│   └── Dockerfile
├── docker-compose.yml
├── Makefile                    # make help lista os comandos disponíveis
├── pyproject.toml              # Config do pytest (backend) e do ruff (repo inteiro)
├── requirements.txt            # Dependências do backend/scripts
└── .env                        # Variáveis de ambiente (não versionado)
```

## 🚀 Começando

### Pré-requisitos
- Python 3.12+ (ou só Docker, se preferir não instalar nada localmente)
- Chave da OpenAI (`OPENAI_API_KEY`)

### Opção 1 — Docker (mais simples)

```bash
# 1. Configure a chave da OpenAI
cp .env.example .env
# edite o .env e defina OPENAI_API_KEY=sua_chave_aqui

# 2. Ingestão dos documentos (só precisa rodar uma vez, ou de novo se docs/ mudar)
docker compose run --rm ingest
# (ou: make docker-ingest)

# 3. Sobe a API e a interface web
docker compose up
# (ou: make docker-up)
```

- API: `http://localhost:8000` (docs interativas em `http://localhost:8000/docs`)
- Interface web: `http://localhost:8501` — abre direto na tela de login/cadastro

As migrações do banco rodam automaticamente no startup do container `backend`. Os dados (ChromaDB e SQLite) ficam em volumes nomeados (`chroma_db`, `analytics_db`), persistindo entre restarts.

#### Atualizando os documentos (calendário novo, resolução revisada, etc.)

`docs/` **não é copiado pra dentro da imagem** — é montado como volume só no serviço `ingest`. Pra atualizar a base de conhecimento:

```bash
# 1. Troque/adicione o PDF em docs/ (mesmo nome ou nome novo, tanto faz)
# 2. Rode a ingestão de novo — ela apaga e reconstrói a coleção do zero,
#    então não fica lixo de versão antiga misturado com a nova
docker compose run --rm ingest

# 3. Reinicie a API pra ela carregar a coleção recriada
docker compose restart backend
```

Não precisa rebuildar a imagem nem mexer em código — só o passo 3 é necessário porque a API mantém o cliente do ChromaDB em memória (carregado uma única vez no startup, por performance) e não percebe sozinha que a coleção foi recriada por outro processo.

### Opção 2 — Manual (sem Docker)

```bash
# 1. Instale as dependências
pip install -r requirements.txt              # backend + scripts (ingest, evaluate)
pip install -r frontend/requirements.txt      # frontend

# 2. Configure as variáveis de ambiente
cp .env.example .env
# edite o .env e defina OPENAI_API_KEY=sua_chave_aqui
```

**PASSO 1 — Ingest (obrigatório, primeira vez):**
```bash
python scripts/ingest.py
```
Carrega os PDFs de `docs/`, divide em chunks, cria embeddings via OpenAI e salva no ChromaDB.

**PASSO 2 — Migrações do banco:**
```bash
cd backend && alembic upgrade head
```

**PASSO 3 — API** (mesmo terminal, dentro de `backend/`):
```bash
python main.py
```
Disponível em `http://localhost:8000`.

**PASSO 4 — Interface Streamlit** (outro terminal):
```bash
cd frontend && streamlit run main.py
```
Disponível em `http://localhost:8501`.

> Também dá pra usar o `Makefile`: `make install`, `make migrate`, `make ingest`, `make run-backend`, `make run-frontend`. `make help` lista tudo.

## 🧪 Testes

```bash
pytest              # suíte do backend, a partir da raiz do repo
cd frontend && pytest   # suíte do frontend
# ou: make test-all
```

Não precisa de `OPENAI_API_KEY` válida nem de rede — tudo que tocaria a API da OpenAI é mockado. CI (GitHub Actions) roda as duas suítes, mais lint (`ruff check` + `ruff format --check`), em todo push/PR para `main`.

Para avaliar a qualidade das respostas do RAG contra um golden set de perguntas com resposta conhecida (isso sim precisa de uma `OPENAI_API_KEY` válida, faz chamadas reais):

```bash
cd backend && python ../scripts/evaluate.py
```

## 🎯 Funcionalidades

- **Autenticação por e-mail institucional**: cadastro/login restrito a e-mails `@ufrn`, autenticação por API key simples
- **Chat Inteligente**: Perguntas e respostas baseadas nos documentos oficiais
- **Guardrail contra alucinação**: verifica se a resposta está de fato fundamentada nos trechos recuperados antes de retorná-la
- **Sistema de Cache**: Respostas frequentes (por hash exato ou por similaridade semântica) são servidas instantaneamente
- **Rate limiting**: protege as rotas que consomem a API da OpenAI (`/ask`) e as de autenticação (`/auth/*`, contra força bruta) contra abuso
- **Dashboard de Analytics**: métricas de uso, cache e feedback, direto na interface
- **Feedback do Usuário**: Sistema de avaliação com 👍/👎
- **Fontes Transparentes**: Mostra quais documentos foram consultados
- **Categorias Organizadas**: Perguntas pré-definidas por categoria

## 📊 Monitoramento

- **Dashboard de Analytics**: aba "📊 Analytics" na interface Streamlit (`frontend/pages/`) — perguntas totais, satisfação, tamanho do cache, taxa de reaproveitamento, distribuição de feedback, perguntas mais frequentes, feedback recente e itens mais acessados do cache. Exige login, igual ao resto do app.
- `GET /api/v1/metrics/`: total de perguntas, respostas cacheadas, feedback positivo/negativo, taxa de satisfação, perguntas mais frequentes.
- `GET /api/v1/cache/stats`: tamanho do cache, total de acessos, entradas mais acessadas.
- Ambas exigem `X-API-Key` (ver [Autenticação](#-autenticação)). Documentação interativa em `http://localhost:8000/docs`.
- Logs de aplicação vão pro stdout/console — `docker compose logs -f backend` (Docker) ou o próprio terminal (`python main.py`, local). Não há persistência de log em arquivo configurada.

## ❗ Solução de problemas

- **Erro "API Offline"**: certifique-se que a API está rodando (`cd backend && python main.py`, ou `docker compose up backend`) e que `API_BASE_URL` (se estiver usando Docker) aponta para o host certo.
- **Respostas caindo sempre no fallback**: confirme que a ingestão rodou com sucesso (`python scripts/ingest.py` ou `docker compose run --rm ingest`) e que a `OPENAI_API_KEY` no `.env` é válida.
- **Erro de API Key da OpenAI**: verifique se `OPENAI_API_KEY` está definida no `.env` (local) ou disponível para o container `backend` (Docker).
- **`401 API key inválida` em qualquer rota**: faça login/cadastro em `/api/v1/auth/login` ou `/api/v1/auth/register` e reenvie a API key recebida no header `X-API-Key`.
- **`422` ao cadastrar**: o e-mail precisa conter `ufrn` no domínio (ex.: `@alunos.ufrn.br`) e a senha precisa ter no mínimo 8 caracteres.

## 📌 Status (WIP)

- RAG
    - [x] Retrieval MMR + guardrail contra alucinação (gate de relevância + checagem de groundedness)
    - [x] Extração de PDF ciente de estrutura (PyMuPDF + chunking por artigo nas resoluções)
    - [x] Cache exato (hash) + cache semântico (similaridade, threshold calibrado)
    - [x] Golden set + script de avaliação de qualidade (`scripts/evaluate.py`)
    - [ ] Reranking / busca híbrida (BM25 + vetorial)
    - [ ] Métricas de qualidade estilo RAGAS (faithfulness, context precision/recall)
- Backend
    - [x] Autenticação (API key + e-mail `@ufrn`), todas as rotas de negócio protegidas
    - [x] Rate limiting (`/ask`, `/auth/*`)
    - [x] Migrações versionadas (Alembic)
    - [x] Testes automatizados (pytest) + CI (GitHub Actions) + lint (Ruff)
    - [ ] Suporte a PostgreSQL validado em produção (config já existe, não testada além do SQLite)
- Frontend
    - [x] Chat, login/cadastro, feedback, perguntas por categoria
    - [x] Dashboard de Analytics (`/metrics` + `/cache/stats`)
    - [ ] Sessão persistente entre reloads (hoje reseta ao fechar a aba)
- Infra
    - [x] Docker Compose (backend + frontend + ingest sob demanda)
    - [x] `docs/` como volume (atualização de documento sem rebuild de imagem)
    - [ ] HTTPS/reverse proxy, health checks, deploy automatizado (CI hoje só testa, não publica imagem)

## 💡 Melhorias futuras sugeridas

| Melhoria | Propósito | Prioridade | Notas |
|---|---|---|---|
| **Reranking + busca híbrida** | Melhorar precisão do retrieval (BM25 pra termos exatos como nº de resolução/data) | Média | Pode ser feito com libs locais (`rank_bm25`, cross-encoder via `sentence-transformers`), sem custo de API extra |
| **Reforço da autenticação** | Sessão persistente (cookie), rotação de API key, verificação de e-mail | Baixa | Verificação por e-mail exige SMTP configurado |
| **Deploy automatizado** | CI publica imagem + faz deploy em push pra `main` | Baixa | Hoje o CI só roda testes/lint |
