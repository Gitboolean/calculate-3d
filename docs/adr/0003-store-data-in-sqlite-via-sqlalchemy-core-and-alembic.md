---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-27"
feature_size:
stage: "00"
ticket: ""
---

# 0003 — Store data in SQLite via SQLAlchemy Core + Alembic, with UUIDv7 IDs and money in integer kopecks

- **Status:** Accepted
- **Date:** 2026-10-27
- **Deciders:** Anton Pohorielov (with Claude, `map-architecture` greenfield session)

## Context

The app persists price settings (filament price per kg, electricity tariff, wear per hour, failure %)
and a catalog of items that stores print parameters — never a final price, which is always recomputed
(brief §10 TOP risk). One local user, a few hundred rows at most. The cost result is a minimum
donation, so it must never be understated by rounding.

## Decision drivers

- Local, single-user, no server to operate (brief §13, ADR 0004).
- SDLC conventions: SQL-first, "DB as dumb storage", timestamped idempotent migrations (`generate-data-model`).
- Money correctness: no float rounding errors; cost rounded up.

## Considered options

Datastore:
1. **SQLite file** — zero ops, backup = copy the file.
2. **PostgreSQL in Docker** — closer to production practice, extra setup for no functional gain here.

Access + migrations:
1. **SQLAlchemy 2 Core + Alembic (SQL-first revisions)** — SQL-shaped, typed, real up/down migrations.
2. **SQLAlchemy ORM + Alembic** — convenient, tempts mixing DB models with domain objects.
3. **Raw `sqlite3` + hand-rolled `.sql` runner** — minimal deps, more manual tooling.

IDs: **UUIDv7 from the app** vs **INTEGER autoincrement**.
Money: **INTEGER kopecks + `Decimal`** vs **decimal strings** vs **float**.

## Decision outcome

**Chosen:** SQLite + SQLAlchemy 2 Core + Alembic; UUIDv7 IDs; money as INTEGER kopecks.
- Alembic revisions are timestamp-named and SQL-first (`op.execute` of the staged `.up.sql` /
  `.down.sql` bodies, verbatim); no autogenerate.
- IDs are generated in code (`uuid.uuid7()`, Python 3.14) and stored as `TEXT`.
- Money columns end in `_kop` (INTEGER); calculations use `decimal.Decimal`; the final cost is rounded
  with `ROUND_CEILING` to whole kopecks.
- No CHECK / TRIGGER / business defaults; `created_at` only; hard delete; `PRAGMA foreign_keys=ON`, WAL.

## Consequences

**Positive**
- Nothing to install or run besides the app; tests use a real temp SQLite file (no mocks, no containers).
- The minimum donation is never understated by float/rounding error.
- Migrations are reversible and reviewed as plain SQL.

**Negative**
- SQLite dialect limits (`ALTER TABLE` is restricted — some changes need table rebuild migrations).
- Moving to a server DB later means re-testing SQL dialect differences.

**Neutral**
- UUIDv7 as TEXT is larger than an integer key — irrelevant at this data size.

## Links

- `docs/idea-brief.md` §9 (edge cases: units, prices per filament), §10 (stale-price risk)
- `docs/architecture-map.md` §Conventions (IDs, Money, Persistence, Migrations), §Datastores
- ADR 0001, ADR 0004
