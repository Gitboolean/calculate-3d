---
id: T21
title: "Відкрити DTO costing через service.py і повертати loc поля для дубля пластику"
layer: "app"
deps: []
acs: ["AC-07", "AC-14c"]
files_hint: ["backend/src/calculate3d/modules/costing", "backend/src/calculate3d/modules/catalog", "backend/tests"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T21 — Відкрити DTO costing через service.py і повертати loc поля для дубля пластику

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-07, AC-14c у [PRD §5](../PRD.md).

## Definition of Done

- [ ] catalog імпортує PlasticUsage/Quote/QuoteInput/SettingsMissingProblem лише з costing.service (re-export), а не з costing.schemas; 422 на дубль пластику має errors[0].loc == ['body','plastics',<i>,'plastic_id'] (openapi.yaml example duplicate_plastic) — integration-тест для /api/costing/quote і /api/catalog/items; make api-check зелений. Знахідки S1-6, S1-3 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** —.
