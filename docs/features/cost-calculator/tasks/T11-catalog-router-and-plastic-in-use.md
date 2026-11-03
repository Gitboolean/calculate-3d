---
id: T11
title: "Відкрити /api/catalog/items і підключити перевірку використання пластику в pricing (AC-03)"
layer: "ports"
deps: ["T7", "T8", "T10"]
acs: ["AC-03", "AC-10", "AC-11", "AC-12", "AC-13", "AC-14", "AC-14b", "AC-14c", "AC-15"]
files_hint: ["backend/src/calculate3d/modules/catalog/router.py", "backend/src/calculate3d/modules/pricing/router.py", "backend/src/calculate3d/main.py", "backend/tests/integration/test_catalog_api.py", "backend/tests/integration/test_pricing_api.py", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "L"
status: "done"
---

# T11 — Відкрити /api/catalog/items і підключити перевірку використання пластику в pricing (AC-03)

## Why

Операції `listItems`, `createItem`, `getItem`, `updateItem`, `deleteItem` у [openapi.yaml](../contracts/openapi.yaml); [ADR-0005](../adr/0005-split-feature-into-pricing-costing-catalog-modules.md) (роутер `pricing` підставляє `catalog.service.item_names_using_plastic`); [sad.md](../sad.md) §6 «Critical flow 3». Критерії: AC-03, AC-10, AC-11, AC-12, AC-13, AC-14, AC-14b, AC-14c, AC-15 у [PRD §5](../PRD.md).

## What

- `catalog/router.py` (`prefix="/api/catalog"`), `GET /items?q=`, `POST`, `GET/PUT/DELETE /items/{item_id}` зі статусами й `responses=` з контракту.
- `pricing/router.py`: `deletePlastic` передає `catalog.service.item_names_using_plastic` замість заглушки з T7.
- Підключити роутер; `make api-types`.

## Definition of Done

- [ ] Інтеграційні тести: AC-03 (409 з `items: ["Органайзер", "Підставка"]`, після видалення виробу пластик видаляється), AC-10, AC-11, AC-12 (`?q=тризуб`), AC-13 (11525 → 13505), AC-14 / AC-14b / AC-14c (після 422/409 GET повертає старі параметри), AC-15 (204, потім 404 `catalog.item_not_found`).
- [ ] `make check` зелений.

## Notes

- **Blocked by:** [T7](./T7-pricing-router.md), [T8](./T8-costing-quote-endpoint.md), [T10](./T10-catalog-service.md).
- Це єдине місце, де `pricing` залежить від `catalog`, і лише на рівні роутера. Через це T6/T7 не чекають каталог.
