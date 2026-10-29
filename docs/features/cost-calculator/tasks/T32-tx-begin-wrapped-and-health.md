---
id: T32
title: "Брати BEGIN IMMEDIATE через SQLAlchemy і не блокувати health-ping"
layer: "infra"
deps: []
acs: ["AC-03", "AC-14b"]
files_hint: ["backend/src/calculate3d/core/db.py", "backend/src/calculate3d/modules/health/repo.py", "backend/tests/integration"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T32 — Брати BEGIN IMMEDIATE через SQLAlchemy і не блокувати health-ping

## Why

Follow-up з рев'ю [review-2026-10-29-r2](../_review/review-2026-10-29-r2.md). Критерії: AC-03, AC-14b у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Помилка BEGIN IMMEDIATE (зайнятий lock, read-only файл) приходить як SQLAlchemyError; health-ping не бере write-lock; integration-тест: друге з'єднання тримає BEGIN IMMEDIATE → GET /api/health повертає 200 db: "ok" (не 500; під WAL читання проходить, зайнята БД — не «down»); тести статистики запитів і test_tx_serialization лишаються зеленими; make api-check зелений. Знахідка R2-3 у docs/features/cost-calculator/_review/review-2026-10-29-r2.md.

## Notes

- **Blocked by:** —.
