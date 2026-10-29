---
id: T25
title: "Серіалізувати перевірку і запис у транзакції та перекладати FK IntegrityError у доменні помилки"
layer: "infra"
deps: ["T22"]
acs: ["AC-03", "AC-14b"]
files_hint: ["backend/src/calculate3d/core/db.py", "backend/src/calculate3d/modules/pricing", "backend/src/calculate3d/modules/catalog", "backend/tests"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T25 — Серіалізувати перевірку і запис у транзакції та перекладати FK IntegrityError у доменні помилки

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-03, AC-14b у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Мутуючий запит починає транзакцію до перевірок (BEGIN IMMEDIATE через pysqlite-рецепт SQLAlchemy у create_db_engine); FK IntegrityError у pricing.repo.delete_plastic → pricing.plastic_in_use, у catalog.repo.replace_usage → catalog.plastic_not_found (не 500); тести, що симулюють FK-порушення в обхід сервісної перевірки; make api-check зелений. Знахідка S2-2 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** T22.
