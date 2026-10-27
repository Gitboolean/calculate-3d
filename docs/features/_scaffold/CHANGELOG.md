# Changelog — _scaffold

## _scaffold — runnable project foundation for calculate-3d (2026-10-27)

**What:** an empty but working calculate-3d app that is ready for the first real feature. One command
(`make run`) migrates a local SQLite database, builds the web UI and serves the UI and the API from a
single process on `127.0.0.1:8000`. The home page shows API and database health. One command
(`make check`) runs the same gate as CI: Python lint, strict types and tests, web lint (including FSD
boundaries via Steiger), types, tests and build, plus a check that the web's API types match the
backend OpenAPI.

**Why:** the product ([idea brief](../../idea-brief.md)) is a local, single-user tool that
computes the cost price of a 3D print. Every later feature needs the same base: a place for modules,
a database with migrations, a typed API contract the UI is built from, and one error shape. This
scaffold fixes those decisions once, so features add code and do not have to argue about structure.
The load-bearing decisions:
- [ADR 0001](../../adr/0001-use-python-fastapi-and-react-vite-stack.md): Python/FastAPI + React/Vite.
- [ADR 0002](../../adr/0002-organize-as-modular-monolith-with-simple-layers.md): a modular monolith
  with router → service → repo layers.
- [ADR 0003](../../adr/0003-store-data-in-sqlite-via-sqlalchemy-core-and-alembic.md): SQLite via
  SQLAlchemy Core and SQL-first Alembic migrations, app-generated UUIDv7 IDs, money as integer kopecks.
- [ADR 0004](../../adr/0004-run-local-only-without-authentication.md): local-only, bound to
  `127.0.0.1`, no auth.

Conventions live in [`docs/architecture-map.md`](../../architecture-map.md) and the root, backend and
web `CLAUDE.md` files.

**How to use:**
```sh
make install   # uv sync --locked + npm ci
make run       # http://127.0.0.1:8000 (UI + API, one process)
make dev       # API with --reload on :8000 + Vite on :5173
make check     # what CI runs; must be green before a commit
curl http://127.0.0.1:8000/api/health   # {"status":"ok","db":"ok"}
```
Errors anywhere in the API (404, 405, 422, domain `AppError`s and unexpected 500s) come back as RFC
9457 `application/problem+json` with a stable `code`. Each request gets one DB transaction through
`ConnectionDep`. The transaction commits before the response is sent, so a failed commit becomes a
500, never a false 200. A new module starts as a copy of `modules/health/`.

**Operational notes:**
- Migration: adds `20261027_2215_initial` (an empty baseline revision). `make run` applies it
  automatically, and `make migrate-down` reverts it cleanly. The DB file is
  `backend/var/calculate3d.db` by default (gitignored); override it with `CALC3D_DATABASE_URL`.
- Feature flag / config: none. The only setting is `CALC3D_DATABASE_URL`. The bind address is fixed
  at `127.0.0.1` and cannot be configured (ADR 0004).
- Rollback: this is the first change on `main`, so a rollback means not merging the branch. Locally,
  `make migrate-down` and then delete `backend/var/`.

**Acceptance criteria delivered:** the Definition of Done of every scaffold task S1–S7 (backend app
factory, test and type gates, SQLite and migrations, the FSD web app, the Makefile with
single-process `make run`, CI and the CLAUDE.md files), plus review fixes R1–R14 from 4 review rounds.
The final round, [`review-2026-10-27-r5.md`](_review/review-2026-10-27-r5.md), ended in PASS.
