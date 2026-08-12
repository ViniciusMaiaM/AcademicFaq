.DEFAULT_GOAL := help

.PHONY: help install install-frontend migrate ingest run-backend run-frontend \
        test test-frontend test-all lint format format-check \
        docker-build docker-up docker-down docker-ingest docker-logs docker-restart-backend \
        clean

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

## --- Setup local (sem Docker) ---

install: ## Instala as dependências do backend/scripts (inclui pytest/ruff)
	pip install -r requirements.txt

install-frontend: ## Instala as dependências do frontend (produção, sem pytest)
	pip install -r frontend/requirements-dev.txt

migrate: ## Roda as migrações do banco (cd backend && alembic upgrade head)
	cd backend && alembic upgrade head

ingest: ## Roda a ingestão dos documentos de docs/ pro ChromaDB (precisa de OPENAI_API_KEY válida)
	python scripts/ingest.py

run-backend: ## Sobe a API (cd backend && python main.py) — porta 8000
	cd backend && python main.py

run-frontend: ## Sobe a interface Streamlit (cd frontend && streamlit run main.py) — porta 8501
	cd frontend && streamlit run main.py

## --- Testes ---

test: ## Roda a suíte de testes do backend
	pytest -v

test-frontend: ## Roda a suíte de testes do frontend
	cd frontend && pytest -v

test-all: test test-frontend ## Roda as duas suítes de teste (backend + frontend)

## --- Qualidade de código ---

lint: ## Roda o ruff check (lint) no repo inteiro
	ruff check .

format: ## Reformata o repo inteiro com ruff format
	ruff format .

format-check: ## Confere formatação sem alterar arquivos (usado no CI)
	ruff format --check .

## --- Docker ---

docker-build: ## Builda as imagens do backend e frontend
	docker compose build

docker-up: ## Sobe backend + frontend (primeiro plano)
	docker compose up

docker-down: ## Derruba os containers (mantém os volumes com os dados)
	docker compose down

docker-ingest: ## Roda a ingestão dentro do container (precisa de OPENAI_API_KEY válida no .env)
	docker compose run --rm ingest

docker-restart-backend: ## Reinicia só o backend — necessário depois de docker-ingest, pra recarregar a coleção
	docker compose restart backend

docker-logs: ## Acompanha os logs dos containers
	docker compose logs -f

## --- Limpeza ---

clean: ## Remove caches (__pycache__, .pytest_cache, .ruff_cache)
	find . -type d -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} +
	rm -rf .pytest_cache frontend/.pytest_cache .ruff_cache
