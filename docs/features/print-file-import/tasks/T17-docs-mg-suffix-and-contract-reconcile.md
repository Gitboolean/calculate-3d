---
id: T17
title: "Документація: суфікс *_mg у CLAUDE.md, закриття D1/D3 у api-sync-report"
layer: "docs"
deps: ["T10", "T16"]
acs: ["AC-03"]
files_hint: ["CLAUDE.md", "backend/CLAUDE.md", "docs/features/print-file-import/contracts/api-sync-report.md"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T17 — Документація: суфікс *_mg у CLAUDE.md, закриття D1/D3 у api-sync-report

## Why

Accepted debt [sad.md](../sad.md) §11 («`CLAUDE.md` не називає `*_mg`») і deferrals D1/D3 [api-sync-report.md](../contracts/api-sync-report.md). AC-03 — правило, яке описує `*_mg`.

## What

- `CLAUDE.md` § Money/units (+ `backend/CLAUDE.md`, якщо дублює): «міліграми `*_mg` — лише точна витрата у відповіді розбору; у БД і `costing` — `*_cg`» ([ADR 0004](../adr/0004-compose-quote-rows-in-the-web-from-exact-milligrams.md)).
- `api-sync-report.md`: D1, D3 → closed з посиланням на тести; далі — `/sdlc:api-forge print-file-import --reconcile` вручну.

## Definition of Done

> CLAUDE.md § Money/units називає суфікс *_mg (лише у відповіді розбору), api-sync-report.md позначає D1 і D3 закритими з посиланням на тести T6/T8, а make check зелений.

- [ ] `CLAUDE.md` оновлено; `make check` зелений
- [ ] `api-sync-report.md` D1/D3 закриті; Verdict лишається `PASS (with deferrals)` лише через D4 (spectral)

## Notes

Оновлення `docs/architecture-map.md` (застарів, [sad.md](../sad.md) §11) — окремий `/sdlc:map-architecture`, не ця задача.
