---
id: T9
title: "Додати catalog tables + repo: вироби з рядками витрати, пакетне читання без N+1"
layer: "infra"
deps: ["T1"]
acs: ["AC-03", "AC-10", "AC-12", "AC-14b", "AC-15"]
files_hint: ["backend/src/calculate3d/modules/catalog/__init__.py", "backend/src/calculate3d/modules/catalog/tables.py", "backend/src/calculate3d/modules/catalog/repo.py", "backend/tests/factories.py", "backend/tests/integration/test_catalog_repo.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T9 — Додати catalog tables + repo: вироби з рядками витрати, пакетне читання без N+1

## Why

[data-model.md](../data-model.md) (`items`, `item_plastics`, індекси), [ADR-0003](../adr/0003-recompute-catalog-prices-on-every-read.md) (фіксована кількість запитів), [sad.md](../sad.md) §6 «Critical flow 2», «Зберегти виріб», «Видалити виріб». Критерії: AC-03, AC-10, AC-12, AC-14b, AC-15 у [PRD §5](../PRD.md).

## What

- `tables.py` — `items`, `item_plastics` на `core.db.metadata`.
- `repo.py`: `insert_item`, `update_item`, `replace_usage(item_id, rows)` (DELETE + INSERT), `get_item` (+ рядки), `list_items_with_usage()` (2 запити на весь каталог), `delete_item`, `find_by_name_key`, `item_names_using_plastic(plastic_id)` (через `idx_item_plastics_plastic_id`).
- `tests/factories.py`: `make_item`, `seed_catalog_volume(items=1000, plastics=50, seed=…)`.

## Definition of Done

- [ ] Лічильник `before_cursor_execute`: `list_items_with_usage()` на 1 000 виробів = 2 запити.
- [ ] `delete_item` → рядки `item_plastics` зникли (CASCADE); `DELETE FROM plastics` з використаним пластиком → `IntegrityError` (RESTRICT).
- [ ] `make api-check` зелений.

## Notes

- **Blocked by:** [T1](./T1-promote-migrations.md).
- Спільний `tests/factories.py` з T6 → одна черга. Repo `catalog` **не** читає таблицю `plastics` (лише FK) — ADR-0005.
