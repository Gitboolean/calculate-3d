---
id: T38
title: "Узгодити test-plan, контракт, коментарі й PRD з межами T34 і перезвірити api-sync-report"
layer: "docs"
deps: []
acs: ["AC-02", "AC-05", "AC-07"]
files_hint: ["docs/features/cost-calculator/test-plan.md", "docs/features/cost-calculator/contracts/openapi.yaml", "docs/features/cost-calculator/contracts/api-sync-report.md", "docs/features/cost-calculator/PRD.md", "backend/src/calculate3d/modules/costing/schemas.py", "backend/src/calculate3d/core/db.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T38 — Узгодити test-plan, контракт, коментарі й PRD з межами T34 і перезвірити api-sync-report

## Why

Follow-up з рев'ю [review-2026-10-30](../_review/review-2026-10-30.md). Критерії: AC-02, AC-05, AC-07 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] test-plan.md:69 замінено рядками меж для AC-02/AC-05/AC-07 (значення на межі приймається, понад межу — відхиляється з повідомленням, що називає максимум) з посиланнями на parse.test.ts / validate.test.ts / fields.test.ts / test_input_bounds.py; openapi.yaml:529 msg = живий текст («Input should be greater than or equal to 1»), опис ItemInvalid згадує межі; коментар costing/schemas.py:9 без «no practical limit»; PRD.md:102 — кома перед «дробові потужність»; коментар core/db.py:37 каже «no transaction (driver autocommit); single-statement reads only»; /sdlc:api-forge cost-calculator --reconcile — Verdict PASS; make check зелений. Знахідки R3-1, R3-5, R3-8 у docs/features/cost-calculator/_review/review-2026-10-30.md.

## Notes

- **Blocked by:** —.
