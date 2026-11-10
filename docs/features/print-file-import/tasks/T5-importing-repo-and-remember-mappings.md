---
id: T5
title: "importing.repo: пошук зіставлень за (назва, колір) і upsert; remember_mappings у service"
layer: "infra"
deps: ["T1"]
acs: ["AC-07", "AC-08", "AC-10", "AC-11"]
files_hint: ["backend/src/calculate3d/modules/importing/repo.py", "backend/src/calculate3d/modules/importing/service.py", "backend/tests/integration/test_importing_repo.py", "backend/tests/unit/test_importing_service.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T5 — importing.repo: пошук зіставлень за (назва, колір) і upsert; remember_mappings у service

## Why

Access patterns 1–2 з [data-model.md](../data-model.md) і контракт `remember_mappings(conn, mappings)` з [ADR 0003](../adr/0003-remember-filament-mappings-in-the-item-save-transaction.md). AC-07 (запам'ятати), AC-08 (замінити), AC-10 (кілька пар → один пластик), AC-11 (видалений пластик не підставляється) у [PRD §5](../PRD.md).

## What

- `repo.py`: `find_mappings(conn, pairs) -> dict[(name, color), plastic_id]` (`(…) IN (VALUES …)` під `uq_filament_mappings_name_color`); `upsert_mappings(conn, rows)` — `INSERT … ON CONFLICT (filament_name, filament_color) DO UPDATE SET plastic_id = excluded.plastic_id`, `id` з `new_id()`.
- FK `IntegrityError` → repo-виняток `MappingPlasticMissing(plastic_id)` (як у `catalog/repo.py`).
- `service.py`: `remember_mappings(conn, mappings)` + доменна помилка `ImportPlasticNotFound` (`importing.plastic_not_found`, 422 + `field`; [openapi.yaml](../contracts/openapi.yaml)). Приймає `Connection` викликача — власної транзакції не відкриває.

## Definition of Done

> Інтеграційні тести repo показують: пошук до 32 пар повертає plastic_id лише для збережених пар, upsert замінює plastic_id і зберігає id/created_at, а FK-порушення стає repo-винятком, який remember_mappings мапить на доменну помилку.

- [ ] Інтеграційний тест (реальна SQLite, мігрована Alembic): upsert тієї самої пари з іншим `plastic_id` змінює лише `plastic_id`; дві різні пари → один пластик зберігаються обидві (AC-10)
- [ ] Після видалення пластику `find_mappings` не повертає його пару (AC-11)
- [ ] Юніт-тест service: repo-виняток → `ImportPlasticNotFound` з `field`; `make api-check` зелений

## Notes

`importing.service` ще не має `parse_slicer_file` — його додає T6 (той самий файл → одна смуга з T6). `test_module_boundaries` має лишитися зеленим: `importing` не імпортує `catalog`.
