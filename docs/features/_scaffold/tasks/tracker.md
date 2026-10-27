# Tracker — `_scaffold`

| Task | Title | Status | Commit |
|---|---|---|---|
| S1 | Backend project: uv + Python 3.14 + FastAPI app factory, core/ | done | 30d65ed |
| S2 | Backend test harness + lint/type gates + health smoke | done | adc4571 |
| S3 | SQLite engine with pragmas + Alembic timestamped SQL-first migrations | done | 4cb8594 |
| S4 | Web app (Vite + React + TS, FSD, Tailwind + shadcn/ui, TanStack Query) | done | 9549b4e |
| S5 | Root Makefile + single-process `make run` | done | 05313c0 |
| S6 | CI workflow running `make check` | done | 861205c |
| S7 | Root, backend and web CLAUDE.md | done | 13f3c2b |
| R1 | Review fix: health router → service → repo, db "down" | done | 4e77ee2 |
| R2 | Review fix: every error is problem+json | done | 2ba7102 |
| R3 | Review fix: always bind 127.0.0.1 | done | 6dc5c67 |
| R4 | Review fix: `uv sync --locked` | done | 8bee718 |
| R5 | Review fix: schema.d.ts drift check in `make check` | done | 9902f33 |
| R6 | Review fix: health router depends only on its service; layering documented | todo | |
| R7 | Review fix: `create_app(settings)` uses `settings.database_url` | todo | |
| R8 | Review fix: OpenAPI dump to a temp file | todo | |
| R9 | Review fix: HomePage db-down test | todo | |

R1–R5 come from `_review/review-2026-10-27.md` (findings 1–9).
R6–R9 come from `_review/review-2026-10-27-r2.md` (findings 10–13).
