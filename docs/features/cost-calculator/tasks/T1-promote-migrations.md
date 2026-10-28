---
id: T1
title: "Перенести 4 staged-міграції в ланцюжок Alembic і задокументувати суфікси одиниць"
layer: "migration"
deps: []
acs: ["AC-03", "AC-09", "AC-15"]
files_hint: ["docs/features/cost-calculator/migrations/20261028120000_create_plastics", "docs/features/cost-calculator/migrations/20261028120001_create_price_settings", "docs/features/cost-calculator/migrations/20261028120002_create_items", "docs/features/cost-calculator/migrations/20261028120003_create_item_plastics", "backend/tests/integration/test_migrations.py", "CLAUDE.md"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T1 — Перенести 4 staged-міграції в ланцюжок Alembic і задокументувати суфікси одиниць

## Why

Таблиці `plastics`, `price_settings`, `items`, `item_plastics` описані в [data-model.md](../data-model.md) § Staged migrations; FK RESTRICT/CASCADE — страховка під AC-03 / AC-15, відсутній рядок `price_settings` = «не задано» (AC-09). Критерії: AC-03, AC-09, AC-15 у [PRD §5](../PRD.md).

## What

- Кожна staged-пара `.up.sql`/`.down.sql` → окрема ревізія `backend/migrations/versions/YYYYMMDD_HHMM_<slug>.py`, у ланцюжку після `20261027_2215_initial` у порядку 1 → 4.
- Кожне SQL-твердження — свій `op.execute("""…""")` (sqlite3 виконує одне твердження за виклик); SQL переноситься дослівно.
- `CLAUDE.md` § Physical units: додати `*_cg`, `*_permille`, `*_h` (борг із sad §11 і data-model «Відхилення від конвенцій»).

## Definition of Done

- [ ] Staged-міграції перенесено в живий `backend/migrations/versions/`; `alembic upgrade head` → `downgrade base` → `upgrade head` чисті (наявний `test_migrations.py`).
- [ ] Тест: `PRAGMA foreign_key_list(item_plastics)` показує RESTRICT на `plastics` і CASCADE на `items`; є `idx_item_plastics_plastic_id`, `uq_plastics_name_key`, `uq_items_name_key`.
- [ ] `CLAUDE.md` перелічує суфікси `_cg`, `_permille`, `_h`.
- [ ] `make api-check` зелений.

## Notes

- **Blocked by:** —.
- Лінія `migration` серіалізується. `tables.py` тут **не** створюються — вони з'являються разом із repo (T6, T9).
