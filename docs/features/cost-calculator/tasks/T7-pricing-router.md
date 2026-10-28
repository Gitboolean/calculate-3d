---
id: T7
title: "Відкрити /api/pricing: CRUD пластиків і GET/PUT налаштувань цін"
layer: "ports"
deps: ["T6"]
acs: ["AC-01", "AC-02", "AC-04", "AC-05"]
files_hint: ["backend/src/calculate3d/modules/pricing/router.py", "backend/src/calculate3d/main.py", "backend/tests/integration/test_pricing_api.py", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T7 — Відкрити /api/pricing: CRUD пластиків і GET/PUT налаштувань цін

## Why

Операції `listPlastics`, `createPlastic`, `updatePlastic`, `deletePlastic`, `getPriceSettings`, `replacePriceSettings` у [openapi.yaml](../contracts/openapi.yaml); [api-sync-report.md](../contracts/api-sync-report.md) § D («роутери оголошують `responses=`»). Критерії: AC-01, AC-02, AC-04, AC-05 у [PRD §5](../PRD.md).

## What

- `router.py` з `APIRouter(prefix="/api/pricing")`, `ConnectionDep`; статуси й `responses=` з problem-схемами точно як у контракті (201/200/204, 404, 409, 422).
- `GET /settings` до першого збереження → як у контракті (`getPriceSettings`).
- `deletePlastic` поки передає `item_names_using=lambda _: []`; справжню перевірку підключає T11.
- Підключити в `create_app()`; `make api-types` → оновлений `schema.d.ts`.

## Definition of Done

- [ ] Інтеграційні тести: AC-01 (201 + у списку), AC-02 (`409 pricing.name_taken`, `422 validation_error`), AC-04 (PUT → GET повертає всі поля + `wear_per_hour_kop: 700`), AC-05 (422 → жодне поле не змінилося), 404 `pricing.plastic_not_found`.
- [ ] `/openapi.json` містить ці 6 операцій з оголошеними error-відповідями.
- [ ] `make check` (зокрема `api-types-check`) зелений.

## Notes

- **Blocked by:** [T6](./T6-pricing-service.md).
- Черга `schema.d.ts` / `main.py` спільна з T8 і T11, тож вони йдуть послідовно.
