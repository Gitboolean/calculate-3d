---
id: T1
title: "Промоутнути staged-міграцію filament_mappings і дзеркало importing/tables.py"
layer: "migration"
deps: []
acs: ["AC-07", "AC-11"]
files_hint: ["docs/features/print-file-import/migrations/20261110120000_create_filament_mappings.up.sql", "docs/features/print-file-import/migrations/20261110120000_create_filament_mappings.down.sql", "backend/src/calculate3d/modules/importing/__init__.py", "backend/src/calculate3d/modules/importing/tables.py", "backend/tests/factories.py", "backend/tests/integration/test_migrations.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T1 — Промоутнути staged-міграцію filament_mappings і дзеркало importing/tables.py

## Why

Таблиця зіставлень — єдина нова сутність фічі ([data-model.md](../data-model.md) § Aggregate `importing`, [ADR 0003](../adr/0003-remember-filament-mappings-in-the-item-save-transaction.md), [ADR 0005](../adr/0005-add-an-importing-module-that-owns-the-parser-and-filament-mappings.md)). Каскад FK — механізм AC-11 у [PRD §5](../PRD.md).

## What

- Staged-пару `migrations/20261110120000_create_filament_mappings.{up,down}.sql` перенести дослівно в нову Alembic-ревізію `backend/migrations/versions/YYYYMMDD_HHMM_create_filament_mappings.py` (`down_revision` = поточний head). Кожне SQL-твердження — окремий `op.execute("""…""")`: 3 в `upgrade()`, 3 в `downgrade()` ([data-model.md](../data-model.md) § Staged migrations).
- Створити пакет `modules/importing/` з `tables.py`: `Table("filament_mappings", metadata, …)`, `Index("uq_filament_mappings_name_color", …, unique=True)`, `ForeignKey("plastics.id", ondelete="CASCADE")` — як у `pricing/tables.py`.
- Фабрика `make_filament_mapping(conn, *, plastic_id, filament_name="Bambu PLA Basic @BBL A1M", filament_color="#FFFFFF") -> str` у `backend/tests/factories.py` ([data-model.md](../data-model.md) § Test fixtures).

## Definition of Done

> Ревізія create_filament_mappings проходить upgrade → downgrade → upgrade у test_migrations, а видалення пластику каскадно видаляє його рядок filament_mappings.

- [ ] Staged-пара промоутнута в `backend/migrations/versions/`; `test_migrations` (upgrade → downgrade → upgrade) зелений
- [ ] Інтеграційний тест: `DELETE` пластику видаляє його рядок `filament_mappings` (каскад, AC-11), а вставка дубля `(filament_name, filament_color)` падає з `IntegrityError`
- [ ] `make api-check` зелений

## Notes

Смуга `migration` — серіалізується. `alembic upgrade head` на копії робочої БД не потрібен: таблиця нова, backfill немає.
