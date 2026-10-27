# backend/ — notes for agents

Root conventions: `../CLAUDE.md`. Run everything from here with `uv run` (Python 3.14 via uv).

- Layout: `src/calculate3d/{main.py, core/, modules/<module>/}`; `migrations/` (Alembic);
  `tests/{unit,integration}/`; `var/` holds the local SQLite file (gitignored).
- `create_app(settings=None)` wires error handlers, then module routers, then mounts `web/dist` at
  `/` **last** (only if built) so `/api` routes always win. Add new routers before the mount.
- Tests: `tests/conftest.py` provides a session-scoped `engine` (temp SQLite migrated to head) and a
  `client` fixture that overrides `get_engine` — use `app.dependency_overrides[get_engine]`, never
  the real DB file. Put pure logic tests in `tests/unit`, HTTP/DB tests in `tests/integration`.
  Dispose any engine you create in a test (warnings are errors → leaked connections fail the run).
- New migration: `uv run alembic revision -m "<slug>"` then write SQL in `op.execute("""...""")`;
  extend `tests/integration/test_migrations.py` coverage implicitly (it walks base ↔ head).
- One pytest filter exists on purpose: Starlette's deprecation notice about `httpx` in TestClient.
