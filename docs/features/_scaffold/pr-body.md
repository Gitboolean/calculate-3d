## Summary

Adds the calculate-3d project foundation: a FastAPI backend (modular monolith, SQLite via SQLAlchemy
Core and SQL-first Alembic) and a React/Vite web app (FSD, Tailwind and shadcn/ui, TanStack Query,
types generated from the backend OpenAPI). `make run` serves both from one process on
`127.0.0.1:8000`, and `make check` is the single CI gate. Context:
[idea brief](docs/idea-brief.md) · [changelog](docs/features/_scaffold/CHANGELOG.md).

## Acceptance criteria

The scaffold has no PRD. Its acceptance criteria are the Definition of Done of each task in
`docs/features/_scaffold/tasks/tasks.json`.

- S1: `uv sync` works, `create_app()` imports, and uvicorn binds to 127.0.0.1 ✓
- S2: `GET /api/health` returns 200 `{"status":"ok","db":"ok"}`, an unknown route returns problem+json,
  and ruff and `mypy --strict` are green ✓
- S3: Alembic upgrade → downgrade base → upgrade works on a temp SQLite file, and `foreign_keys=ON`
  and WAL are on for every connection ✓
- S4: web lint, tsc, vitest and build are green, the Home page test passes with mocked health, Steiger
  is clean, and `schema.d.ts` is generated ✓
- S5: `make check` is green, and `make run` serves the UI at `/` and `/api/health` from one process ✓
- S6: `.github/workflows/ci.yml` sets up uv (Python 3.14) and Node 24, runs `make check` and has no
  deploy job ✓
- S7: the root, backend and web `CLAUDE.md` files state the commands and conventions and link
  ADR 0001–0004 ✓
- R1–R14: review fixes (layering, problem+json everywhere, 127.0.0.1 bind, `uv sync --locked`, the
  schema drift check, settings-driven DB URL, transaction commit before the response, and others) ✓

## Design

- Architecture and conventions: `docs/architecture-map.md`
- Decisions: `docs/adr/0001`–`0004` (stack, modular monolith, SQLite/Core/Alembic + IDs + money,
  local-only without auth)
- Tasks: `docs/features/_scaffold/tasks/` (`tasks.json`, `tracker.md`)
- Reviews: `docs/features/_scaffold/_review/` (4 × CHANGES REQUESTED → round 5 **PASS**)
- Migration: `backend/migrations/versions/20261027_2215_initial.py` (an empty baseline)
- There is no PRD, SAD, data model or OpenAPI contract file: this is the greenfield scaffold, and the
  live OpenAPI comes from FastAPI.

## Tasks (SDLC-Task trailers)

```
a18610c R14  fix: get_connection commits before the response; a failed commit renders 500
a17fe30 R13  fix: api-types temp file is removed on INT/TERM under dash
182f12a R12  test: R7 test proves there is no fallback to the default DB URL
e4f61d1 R11  test: get_connection commits on success and rolls back on error
1a668d3 R10  fix: integration tests enter TestClient as a context manager
a730ae1 R9   test: HomePage renders the db-down state
acfaf6f R8   fix: the OpenAPI dump goes to a temp file, never the working tree
bd1ecf8 R7   fix: create_app(settings) uses settings.database_url
1841046 R6   fix: health router depends only on its service; layering exception documented
9902f33 R5   fix: make check fails when schema.d.ts drifts from the backend OpenAPI
6dc5c67 R3   fix: the server always binds 127.0.0.1
2ba7102 R2   fix: every error renders problem+json
8bee718 R4   fix: make install fails on a stale uv.lock (uv sync --locked)
4e77ee2 R1   fix: health follows router → service → repo and reports db down
13f3c2b S7   docs: root, backend and web CLAUDE.md from the foundation conventions
861205c S6   ci: GitHub Actions workflow running make check
05313c0 S5   chore: root Makefile and single-process make run serving web/dist
9549b4e S4   chore: web app (Vite + React + TS, FSD, Tailwind + shadcn/ui, TanStack Query)
adc4571 S2   chore: backend test harness, ruff/mypy gates, GET /api/health smoke
4cb8594 S3   chore: SQLite engine with pragmas + Alembic timestamped SQL-first migrations
30d65ed S1   chore: create backend project (uv, Python 3.14, FastAPI app factory, core/)
```

## Verification

Checked on 2026-10-27 on `feature/scaffold` @ `2f583af`, macOS:

- Unit and integration: pytest 25/25 green (warnings are errors; the integration tests run against
  a real migrated temp SQLite file). Vitest 3/3 green.
- Lint and types: ruff check and format, `mypy --strict`, ESLint, Prettier, Steiger, `tsc -b`, vite
  build and `api-types-check` are all green (`make check` exit 0).
- Ran the feature with `make run` and `CALC3D_DATABASE_URL` pointed at a scratch DB:
  - `GET /api/health` → `200 {"status":"ok","db":"ok"}`
  - `GET /` → 200 `text/html` with `<div id="root">`, and the JS bundle → 200
  - `GET /api/nope` → 404 `application/problem+json`, `code: not_found`
  - `DELETE /api/health` → 405 problem+json with `Allow: GET, HEAD`
  - The listener is `127.0.0.1:8000` only, and the LAN interface address does not answer
  - The `-wal` file is created (WAL is on), and `make migrate-down` → `make migrate` returns to head
    cleanly
  - The default `backend/var/calculate3d.db` was not touched
- Not verified here: the visual render of the Home page in a real browser. It is covered by
  `HomePage.test.tsx` (ok and db-down states). The GitHub Actions run itself is also unverified:
  there is no remote yet, so CI first runs when the branch is pushed.

## Operational notes

- Migration: `20261027_2215_initial` (empty baseline). `make run` applies it; `make migrate-down`
  reverts it.
- Feature flag / config: none. `CALC3D_DATABASE_URL` is optional and defaults to
  `backend/var/calculate3d.db`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
