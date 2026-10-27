# calculate-3d

Local, single-user tool that computes the cost price of a 3D print — the minimum donation in UAH.
Product context: [`docs/idea-brief.md`](docs/idea-brief.md) · architecture: [`docs/architecture-map.md`](docs/architecture-map.md).

## Requirements

- [uv](https://docs.astral.sh/uv/) — installs Python 3.14 for `backend/` (the system Python is not used)
- Node 24+ and npm

## Quick start

```bash
make install   # uv sync + npm ci
make run       # migrate, build the UI, serve UI + API on http://127.0.0.1:8000
```

## Development

| Command | Does |
|---|---|
| `make dev` | API with reload on :8000 + Vite on http://127.0.0.1:5173 (proxies `/api`) |
| `make check` | all gates: `api-check` + `web-check` (exactly what CI runs) |
| `make migrate` / `make migrate-down` | Alembic upgrade head / downgrade one revision |
| `make api-types` | regenerate the web API types from the backend OpenAPI |

The server binds to `127.0.0.1` only and has no authentication (ADR 0004) — do not expose it on a network.
The SQLite database lives in `backend/var/calculate3d.db` (override with `CALC3D_DATABASE_URL`).
