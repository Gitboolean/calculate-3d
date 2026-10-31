---
id: T43
title: "Дописати межі в контракт quoteCost, SAD потік 1, sync-report і задокументувати межу назви 100 символів"
layer: "docs"
deps: ["T42", "T44"]
acs: ["AC-02", "AC-07", "AC-11"]
files_hint: ["docs/features/cost-calculator/contracts/openapi.yaml", "backend/src/calculate3d/modules/costing/router.py", "docs/features/cost-calculator/sad.md", "docs/features/cost-calculator/contracts/api-sync-report.md", "docs/features/cost-calculator/PRD.md", "docs/features/cost-calculator/data-model.md", "docs/features/cost-calculator/test-plan.md"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T43 — Дописати межі в контракт quoteCost, SAD потік 1, sync-report і задокументувати межу назви 100 символів

## Why

Follow-up з рев'ю [review-2026-10-31](../_review/review-2026-10-31.md). Критерії: AC-02, AC-07, AC-11 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] openapi.yaml:297-300 і costing/router.py:25 — опис 422 quoteCost називає межі (понад 10^8 cg, понад 3,6·10^8 с, понад 32 пластики) як ItemInvalid; sad.md:314 alt і рядок покриття :521 містять «понад межу»; api-sync-report.md:87 — межа 10^8 cg; PRD AC-02 і AC-11 — «назва до 100 символів»; data-model.md:76,108 і Name (openapi.yaml:675-677) — «NFC, обрізання пробілів і невидимих символів по краях, потім 1–100 символів»; test-plan.md: рядки AC-02/AC-11 для межі назви з посиланнями на validate.test.ts, name.test.ts, test_input_bounds.py, а рядки :45,55,71 посилаються на тести T42; /sdlc:api-forge cost-calculator --reconcile — Verdict PASS; make check зелений. Знахідки R4-2…R4-5 у docs/features/cost-calculator/_review/review-2026-10-31.md.

## Notes

- **Blocked by:** T42, T44.
