---
id: T10
title: "Реалізувати catalog.service: збереження, редагування, видалення, пошук і перерахунок цін"
layer: "app"
deps: ["T2", "T8", "T9"]
acs: ["AC-10", "AC-11", "AC-12", "AC-13", "AC-14", "AC-14b", "AC-14c", "AC-15"]
files_hint: ["backend/src/calculate3d/modules/catalog/service.py", "backend/src/calculate3d/modules/catalog/schemas.py", "backend/tests/unit/test_catalog_service.py"]
owner: "Anton Pohorielov"
estimate: "L"
status: "done"
---

# T10 — Реалізувати catalog.service: збереження, редагування, видалення, пошук і перерахунок цін

## Why

[sad.md](../sad.md) §6 «Зберегти виріб у каталог», «Critical flow 2», «Відкрити виріб», «Видалити виріб»; [ADR-0003](../adr/0003-recompute-catalog-prices-on-every-read.md), [ADR-0006](../adr/0006-enforce-name-uniqueness-via-casefolded-name-key.md); схеми `ItemInput`, `Item`, `ItemDetail`, `ItemSummary`, `ItemList` у [openapi.yaml](../contracts/openapi.yaml). Критерії: AC-10, AC-11, AC-12, AC-13, AC-14, AC-14b, AC-14c, AC-15 у [PRD §5](../PRD.md).

## What

- `create_item` / `update_item`: trim + `name_key`; зайнята → `catalog.name_taken` (409, `field=name`); невідомий пластик (через `pricing.service`) → `catalog.plastic_not_found` (422); виріб і рядки пишуться в одній транзакції запиту.
- `get_item` → `ItemDetail` з `quote` через `costing.service`; невідомий → `catalog.item_not_found` (404).
- `list_items(q)` → фільтр `core.text.matches`, сортування `core.text.sort_key`, ціни одним `costing.quote_many` (ADR-0003).
- `delete_item`; `item_names_using_plastic(plastic_id)` — публічна функція для роутера `pricing` (AC-03).

## Definition of Done

- [ ] Unit-тести: AC-10 (ціна не зберігається — у repo пишуться лише параметри), AC-11 («брелок-тризуб» → 409), AC-12 (пошук + порядок), AC-13 (нова ціна пластику → нова ціна виробу без змін виробу), AC-14 / AC-14b / AC-14c, AC-15.
- [ ] Сервіс викликає лише `pricing.service` / `costing.service`, не їхні repo/tables (Hard rule CLAUDE.md).
- [ ] `make api-check` зелений.

## Notes

- **Blocked by:** [T2](./T2-core-names-and-problem-extensions.md), [T8](./T8-costing-quote-endpoint.md), [T9](./T9-catalog-repo.md).
- Найбільша backend-задача; якщо перевищує ~500 LOC — винести `list_items` (пошук/сортування/пакетні ціни) окремим PR.
