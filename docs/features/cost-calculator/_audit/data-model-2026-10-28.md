# Audit — generate-data-model · cost-calculator · 2026-10-28

Mode: greenfield (live `backend/migrations/versions/` містить лише порожній baseline `20261027_2215_initial.py`). Size M (з PRD frontmatter `feature_size`; файлу `.size` немає).

## Generated files

- `docs/features/cost-calculator/data-model.md`
- `docs/features/cost-calculator/migrations/20261028120000_create_plastics.up.sql` / `.down.sql`
- `docs/features/cost-calculator/migrations/20261028120001_create_price_settings.up.sql` / `.down.sql`
- `docs/features/cost-calculator/migrations/20261028120002_create_items.up.sql` / `.down.sql`
- `docs/features/cost-calculator/migrations/20261028120003_create_item_plastics.up.sql` / `.down.sql`
- `.claude/rules/migrations.md`: **bootstrap** з baseline курсу + доданий розділ «Repo adaptation — SQLite + Alembic».

Міграції **staged**: їх ще немає в live-дереві `backend/migrations/versions/`. Їх promote-ить `implement-tasks` і під час promote присвоює timestamp ревізії `YYYYMMDD_HHMM_<slug>.py`, зберігаючи порядок 1 → 4.

**Перевірка SQL** на SQLite 3.54 (`foreign_keys=ON`) показала:
- up → повторний up (ідемпотентність) → down → down → up проходять чисто;
- UNIQUE `name_key`, складений PK, FK RESTRICT (відмова видалити використаний пластик), CASCADE (видалення виробу) і singleton-upsert `price_settings` поводяться як заплановано;
- `EXPLAIN QUERY PLAN` для AC-03 і «рядки виробу» показує `SEARCH … USING INDEX`.

**Self-check (4/4 pass):** naming · down reversibility (кожен CREATE TABLE/INDEX має DROP … IF EXISTS) · FK indexes (`item_id` покриває ліва колонка PK, `plastic_id` має `idx_item_plastics_plastic_id`) · forbidden (немає `CHECK`, `TRIGGER`, бізнес-`DEFAULT`, `updated_at`, `deleted_at`).

**Mermaid:** `erDiagram` перевірено структурним lint-ом (fallback). `npx @mermaid-js/mermaid-cli` заблоковано політикою запуску зовнішнього коду, локального `mermaid` у `node_modules` немає. Рекомендація: один раз прогнати `mmdc` вручну.

## Convention divergences

| # | Divergence | Decision |
|---|---|---|
| 1 | Дефолти курсу — Postgres (`UUID`, `TIMESTAMPTZ DEFAULT now()`, `CONCURRENTLY`), репо — SQLite (ADR 0003 проєкту) | Семантику курсу перенесено в SQLite-форму. `now()` у SQLite немає, а `TIMESTAMPTZ`/`UUID` дали б NUMERIC affinity |
| 2 | Курс: `VARCHAR(N)`. Репо (`CLAUDE.md`): «36-char `TEXT`» | `TEXT` (рішення автора). Межа 100 символів для назв — у Pydantic і data-model.md |
| 3 | Курс: PK завжди UUIDv7 | `item_plastics` — складений PK `(item_id, plastic_id)` (рішення автора): дочірні рядки замінюються цілком, а PK водночас тримає «пластик не двічі» |
| 4 | `CLAUDE.md`: staged файли `<NN>_*.up.sql`. Курс: `<YYYYMMDDhhmmss>_<verb>_<entity>` | Дефолт курсу (timestamp). Вміст копіюється дослівно, ім'я змінюється при promote, тож різниця косметична. Варто узгодити рядок у `CLAUDE.md` |
| 5 | `CLAUDE.md` не каже, хто ставить `created_at` | DB-дефолт `strftime('%Y-%m-%dT%H:%M:%fZ','now')` (SQLite-аналог `DEFAULT now()`); застосунок може передавати власне значення |
| 6 | Новий суфікс одиниці `_h` (`printer_lifetime_h`) поза списком `CLAUDE.md` | Найменша допустима одиниця за AC-05 (цілі години), принцип ADR 0004. Додати до боргу SAD §11 разом із `_cg` / `_permille` |
| 7 | `docs/architecture-map.md` застарів: «grams as `INTEGER`/`REAL` `*_g`» | Перемагає ADR 0004 фічі (`usage_cg`). Борг SAD §11: перезапустити `/sdlc:map-architecture` |
| 8 | Baseline rules говорять про golang-migrate і Go `internal/testfixtures/` | У `.claude/rules/migrations.md` додано розділ SQLite/Alembic/Python, а baseline лишено дослівно |

**Promote-time hints для `implement-tasks`:**
- sqlite3 виконує одне твердження за `execute`, тож кожне твердження пари — окремий `op.execute("""…""")`.
- `price_settings.id` — константа `00000000-0000-7000-8000-000000000001` у `pricing`, а не seed.
- `tests/integration/test_migrations.py` уже проходить base ↔ head. Варто додати перевірку, що після head є 4 таблиці, а після base — жодної.

## Drift findings

**Schema-vs-source:** пропущено. Модулів `pricing` / `costing` / `catalog` у `backend/src/calculate3d/modules/` ще немає (є лише `health`, без таблиць), тож `_drift/` не створено.

**Model-vs-spec:**

| PRD / SAD entity | Table | Status |
|---|---|---|
| пластик (US-01, AC-01..03) | `plastics` | ✓ |
| налаштування цін (US-02, AC-04/05/09; SAD §5 «один рядок») | `price_settings` | ✓ |
| виріб (US-04..06) | `items` | ✓ |
| витрата пластику виробу (AC-06b, AC-07, SAD §5 FK RESTRICT/CASCADE) | `item_plastics` | ✓ |
| розрахунок / quote (US-03) | — | ✓ навмисно не зберігається (CONTEXT, ADR 0002) |
| мінімальний донат / ціна виробу | — | ✓ навмисно не зберігається (ADR 0003) |

Таблиць без походження в PRD/SAD немає. Примітка: у SAD немає окремого розділу «§6.4 ER». ER-заготовкою слугували коментарі `tables.py` у SAD §5 і flags у кінці §6, і їх виконано повністю (FK RESTRICT/CASCADE, `name_key`, singleton, індекс за пластиком).

## Breaking changes decomposed

Немає: greenfield, лише `CREATE`.

## Seeds

Немає (bootstrap / lookup не потрібні; `price_settings` порожня до першого збереження за AC-09). Тестові фабрики описано в `data-model.md` § Test fixtures. Код відкладено до `implement-tasks`, бо модулів, які вони імпортують, ще немає.

## TBDs

Немає: `data-model.md` не містить `<!-- TBD -->`.
