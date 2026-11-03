---
id: T31
title: "Типізувати id у path-параметрах як Id (format: uuid) і полагодити контрактний тест параметрів"
layer: "ports"
deps: []
acs: ["AC-16b"]
files_hint: ["backend/src/calculate3d/modules/catalog/router.py", "backend/src/calculate3d/modules/pricing/router.py", "backend/tests/integration/test_contract.py", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T31 — Типізувати id у path-параметрах як Id (format: uuid) і полагодити контрактний тест параметрів

## Why

Follow-up з рев'ю [review-2026-10-29-r2](../_review/review-2026-10-29-r2.md). Критерії: AC-16b у [PRD §5](../PRD.md).

## Definition of Done

- [ ] item_id/plastic_id у catalog/router.py і pricing/router.py типізовані через core/schemas.py Id, живий OpenAPI емітить format: uuid; _path_id_params у test_contract.py зливає path-item- і operation-рівневі parameters і падає, якщо format прибрати; make api-types без ручних правок; make check зелений. Знахідка R2-1 у docs/features/cost-calculator/_review/review-2026-10-29-r2.md.

## Notes

- **Blocked by:** —.
