---
id: T23
title: "Звести живий OpenAPI з контрактом на рівні схем і задекларувати 415 на DELETE"
layer: "ports"
deps: ["T22"]
acs: ["AC-16b"]
files_hint: ["backend/src/calculate3d", "backend/tests/integration/test_contract.py", "docs/features/cost-calculator/contracts", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T23 — Звести живий OpenAPI з контрактом на рівні схем і задекларувати 415 на DELETE

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-16b у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Response- і problem-моделі мають additionalProperties:false (extra='forbid'), *_kop-виходи minimum 0, items/missing minItems 1 (missing uniqueItems), Id format uuid на path-параметрах і plastic_id; 415 UnsupportedMediaType задекларовано на deletePlastic/deleteItem (router + контракт); test_contract.py порівнює components.schemas (required, типи, межі, additionalProperties) і падає на розбіжності; make api-types перегенеровано; make check зелений. Знахідки S1-4, S1-5 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** T22.
