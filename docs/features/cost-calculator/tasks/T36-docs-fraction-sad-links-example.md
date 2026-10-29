---
id: T36
title: "Узгодити SAD з поправкою ADR 0004, повернути ## Links і оновити приклад msg у контракті"
layer: "docs"
deps: []
acs: ["AC-07", "AC-08", "AC-08b"]
files_hint: ["docs/features/cost-calculator/sad.md", "docs/features/cost-calculator/adr/0004-exchange-quantities-as-scaled-integers.md", "docs/features/cost-calculator/contracts/openapi.yaml"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T36 — Узгодити SAD з поправкою ADR 0004, повернути ## Links і оновити приклад msg у контракті

## Why

Follow-up з рев'ю [review-2026-10-29-r2](../_review/review-2026-10-29-r2.md). Критерії: AC-07, AC-08, AC-08b у [PRD §5](../PRD.md).

## Definition of Done

- [ ] sad.md (рядки ~110, 133, 171, 330, 522) описує точні Fraction-проміжні і округлення через Decimal; ADR 0004 знову має розділ ## Links після поправки; приклад msg дубля пластику в contracts/openapi.yaml = "plastic is listed twice" (як у живому API); make check зелений. Знахідки R2-5, R2-6, R2-7 у docs/features/cost-calculator/_review/review-2026-10-29-r2.md.

## Notes

- **Blocked by:** —.
