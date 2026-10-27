---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-27"
feature_size:
stage: "00"
ticket: ""
---

# 0001 — Use Python 3.14 + FastAPI for the API and React + TypeScript + Vite for the UI

- **Status:** Accepted
- **Date:** 2026-10-27
- **Deciders:** Anton Pohorielov (with Claude, `map-architecture` greenfield session)

## Context

calculate-3d is a greenfield, local, single-user tool that computes the cost price (minimum
donation, UAH) of a 3D print (`docs/idea-brief.md` §1, §13). The `/sdlc:scaffold` template
(base-tpl) only ships a Go + React path; the user chose to stay on Python, so the stack is fixed
here instead of copied from a template. Changing the language later is a rewrite.

## Decision drivers

- User preference: Python backend; this is also a learning project for the full SDLC (brief §4).
- Stage 2 of the product parses slicer project files (Bambu Studio / OrcaSlicer `.3mf`, brief §13) —
  needs good zip/XML tooling.
- The SDLC pipeline derives an OpenAPI contract (`api-forge`); a framework that emits OpenAPI from
  typed models keeps code and contract aligned.
- Brief §5: a browser UI on the same machine, no mobile.

## Considered options

1. **Go + React (base-tpl `go-react`)** — ready, CI-tested template; rejected by the user (wants Python).
2. **Python + FastAPI + React/Vite** — typed Pydantic models, generated OpenAPI, light framework.
3. **Python + Django/DRF + React** — batteries included, heavier, imposes its own app structure.
4. **Python + Litestar + React** — similar to FastAPI, smaller community / fewer learning resources.

## Decision outcome

**Chosen:** Option 2. FastAPI's Pydantic-typed endpoints generate the OpenAPI that `api-forge`
locks and that `openapi-typescript` turns into frontend types, so back and front cannot drift; the
Python ecosystem (`zipfile`, `xml.etree`) covers `.3mf` parsing. Tooling: `uv` (deps + Python 3.14),
ruff, `mypy --strict`, pytest. Frontend: React + TypeScript + Vite + Feature-Sliced Design,
Tailwind + shadcn/ui, TanStack Query.

## Consequences

**Positive**
- One source of truth for API types (Pydantic → OpenAPI → TS).
- Python 3.14 gives stdlib `uuid.uuid7()` (ADR 0003) without extra deps.
- Light framework fits the router/service/repo layering of ADR 0002.

**Negative**
- No ready template: the skeleton must be built and verified by `implement-tasks _scaffold`.
- Two toolchains (uv + npm) on the dev machine; system Python 3.9 is unusable — `uv` must manage Python.

**Neutral**
- Async is available but not required (single user); handlers may be sync.

## Links

- `docs/idea-brief.md` §4, §13
- `docs/architecture-map.md` §Stack
- ADR 0002 (module style), ADR 0003 (persistence), ADR 0004 (local-only, no auth)
