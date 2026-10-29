---
id: T37
title: "Дописати асерти test-plan: quote не створює виріб, порожня назва при редагуванні не зберігається"
layer: "tests"
deps: []
acs: ["AC-06", "AC-14c"]
files_hint: ["backend/tests/integration/test_costing_api.py", "backend/tests/integration/test_catalog_api.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T37 — Дописати асерти test-plan: quote не створює виріб, порожня назва при редагуванні не зберігається

## Why

Follow-up з рев'ю [review-2026-10-29-r2](../_review/review-2026-10-29-r2.md). Критерії: AC-06, AC-14c у [PRD §5](../PRD.md).

## Definition of Done

- [ ] test_costing_api.py після успішного quote перевіряє GET /api/catalog/items == {"items": []}; test_rejected_edit_leaves_the_item_unchanged має кейс blank-name (422, GET незмінний); make api-check зелений. Знахідка R2-10 у docs/features/cost-calculator/_review/review-2026-10-29-r2.md.

## Notes

- **Blocked by:** —.
