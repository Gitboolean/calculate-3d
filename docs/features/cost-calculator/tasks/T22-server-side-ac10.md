---
id: T22
title: "Перевіряти на сервері, що виріб має ціну, перед збереженням (AC-10)"
layer: "app"
deps: ["T21"]
acs: ["AC-10"]
files_hint: ["backend/src/calculate3d/modules/catalog", "backend/tests", "docs/features/cost-calculator/contracts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T22 — Перевіряти на сервері, що виріб має ціну, перед збереженням (AC-10)

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-10 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] catalog._save (create і update) до першого запису проганяє той самий розрахунок, що й quote: без налаштувань цін → 409 costing.settings_missing з missing, виріб не створено/не змінено (test-plan row 77); 409 задекларовано на createItem/updateItem у router і contracts/openapi.yaml; integration-тест; make api-check зелений. Знахідка S1-1 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** T21.
