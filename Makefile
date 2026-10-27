# calculate-3d — one entry point for humans, agents and CI (CI runs exactly `make check`).
.DEFAULT_GOAL := help
SHELL := /bin/bash

API := cd backend &&
WEB := cd web &&

.PHONY: help install dev run check api-check web-check migrate migrate-down api-types

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-13s %s\n", $$1, $$2}'

install: ## Install backend (uv) and web (npm ci) dependencies
	$(API) uv sync
	$(WEB) npm ci

dev: ## API with --reload on :8000 + Vite on :5173 (proxies /api)
	@trap 'kill 0' EXIT; \
	($(API) uv run uvicorn calculate3d.main:create_app --factory --reload --host 127.0.0.1 --port 8000) & \
	($(WEB) npm run dev) & \
	wait

run: migrate ## Build the UI and serve UI + API from one process on 127.0.0.1:8000
	$(WEB) npm run build
	$(API) uv run calculate3d

check: api-check web-check ## Everything CI runs

api-check: ## ruff lint + format check, mypy --strict, pytest
	$(API) uv run ruff check
	$(API) uv run ruff format --check
	$(API) uv run mypy --strict src
	$(API) uv run pytest

web-check: ## ESLint + Prettier + Steiger, tsc, vitest, vite build
	$(WEB) npm run lint
	$(WEB) npx tsc -b --noEmit
	$(WEB) npx vitest run
	$(WEB) npm run build

migrate: ## alembic upgrade head
	$(API) uv run alembic upgrade head

migrate-down: ## alembic downgrade -1
	$(API) uv run alembic downgrade -1

api-types: ## Regenerate web/src/shared/api/schema.d.ts from the backend OpenAPI
	$(WEB) npm run api:types
