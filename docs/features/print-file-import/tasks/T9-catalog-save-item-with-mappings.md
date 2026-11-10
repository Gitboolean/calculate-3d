---
id: T9
title: "catalog: ItemInput.filament_mappings і remember_mappings у транзакції збереження виробу"
layer: "app"
deps: ["T5"]
acs: ["AC-05", "AC-06", "AC-07", "AC-08", "AC-10"]
files_hint: ["backend/src/calculate3d/modules/catalog/schemas.py", "backend/src/calculate3d/modules/catalog/service.py", "backend/tests/unit/test_catalog_service.py", "backend/tests/integration/test_catalog_api.py", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T9 — catalog: ItemInput.filament_mappings і remember_mappings у транзакції збереження виробу

## Why

«Все або нічого» з [ADR 0003](../adr/0003-remember-filament-mappings-in-the-item-save-transaction.md); Critical flow 2 і Flow 6 [sad.md](../sad.md) §6; операції `createItem` / `updateItem` (changed) у [openapi.yaml](../contracts/openapi.yaml). AC-05…AC-08, AC-10 у [PRD §5](../PRD.md).

## What

- `catalog/schemas.py`: `ItemInput.filament_mappings: list[FilamentMappingInput]` (0–32, дублікат пари → `validation_error`), тип — з `importing.schemas` через публічний інтерфейс модуля.
- `catalog/service.py`: `create_item` / `update_item` після запису виробу викликають `importing.service.remember_mappings(conn, data.filament_mappings)` на тому самому `Connection` (одна транзакція `BEGIN IMMEDIATE`). Відповідь `Item` не змінюється.
- `make api-types` → оновлений `schema.d.ts`.

## Definition of Done

> Інтеграційні тести catalog показують, що createItem/updateItem із filament_mappings зберігають виріб і зіставлення разом, а 409 catalog.name_taken чи 422 importing.plastic_not_found не лишають ні виробу, ні змін виробу, ні жодного зіставлення.

- [ ] Інтеграційно: збереження з двома різними парами → один пластик зберігає обидва зіставлення (AC-10); повторне збереження з іншим пластиком для пари замінює його, інші вироби не змінюються (AC-08)
- [ ] `409 catalog.name_taken` і `422 importing.plastic_not_found` (пластик видалено між імпортом і збереженням) → у `filament_mappings` нуль нових рядків, виріб незмінний (AC-06, ADR 0003)
- [ ] Без `filament_mappings` поведінка етапу 1 не змінюється (наявні тести зелені)
- [ ] `test_module_boundaries` зелений (`catalog → importing` лише через `service.py`); `make check` зелений

## Notes

Ділить `schema.d.ts` з T8 (одна смуга). Не пускати `importing.tables`/`repo` у `catalog` — порушення ADR 0002 проєкту.
