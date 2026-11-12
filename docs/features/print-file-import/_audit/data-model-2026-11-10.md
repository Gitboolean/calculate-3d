# Audit — generate-data-model · print-file-import · 2026-11-10

Mode: greenfield-delta. Фіча додає лише нову таблицю, ALTER наявних таблиць немає. Live-дерево `backend/migrations/versions/` має 5 ревізій етапу 1, head — `65f15a51514f` (`create_item_plastics`). Розмір M (з PRD frontmatter `feature_size`; файлу `.size` немає).

## Generated files

- `docs/features/print-file-import/data-model.md`
- `docs/features/print-file-import/migrations/20261110120000_create_filament_mappings.up.sql` / `.down.sql`

Міграції **staged**: у live-дереві `backend/migrations/versions/` їх ще немає. Їх promote-ить `implement-tasks` і під час promote дає ревізії timestamp `YYYYMMDD_HHMM_create_filament_mappings.py` з `down_revision` = head на той момент.

`.claude/rules/migrations.md` уже існує (bootstrap був в етапі 1), тож цього разу файл не змінювався.

**Перевірка SQL** на SQLite 3.54 (`foreign_keys=ON`, перед цим застосовано staged `create_plastics` етапу 1):
- up → повторний up (ідемпотентність) → down → повторний down → up проходять чисто;
- upsert `ON CONFLICT (filament_name, filament_color) DO UPDATE SET plastic_id = excluded.plastic_id` замінює пластик і зберігає `id` наявного рядка (AC-08);
- `bambu PLA…` і `Bambu PLA…` з тим самим кольором — два різні рядки: ключ чутливий до регістру (AC-09);
- `DELETE FROM plastics` каскадом видаляє лише зіставлення цього пластику (AC-11);
- INSERT з `plastic_id` видаленого пластику → `FOREIGN KEY constraint failed` (SAD §6 потік 6, гілка «пластик тим часом видалено»);
- `EXPLAIN QUERY PLAN` для пошуку за `(назва, колір)`, зокрема у формі `IN (VALUES …)`, показує `SEARCH … USING INDEX uq_filament_mappings_name_color`.

**Self-check (4/4 pass):**
- naming: таблиця `filament_mappings` (plural snake_case), файл `<timestamp>_create_filament_mappings`;
- down reversibility: 2 × `CREATE INDEX` + `CREATE TABLE` ↔ 2 × `DROP INDEX IF EXISTS` + `DROP TABLE IF EXISTS` у зворотному порядку;
- FK indexes: `plastic_id REFERENCES plastics(id)` → `idx_filament_mappings_plastic_id`;
- forbidden: grep `CHECK (` / `CREATE TRIGGER` / `DEFAULT '` / `updated_at` / `deleted_at` нічого не знаходить.

**Mermaid:** `erDiagram` перевірено структурним lint-ом (fallback: гліфи кардинальності й рядки `type name [PK|FK|UK] "comment"`). `mmdc` немає ні глобально, ні в `web/node_modules`. Рекомендація з етапу 1 та сама: один раз прогнати `mmdc` вручну.

## Convention divergences

| # | Divergence | Decision |
|---|---|---|
| 1 | Дефолти курсу — Postgres (`UUID`, `TIMESTAMPTZ`, `VARCHAR(N)`), репо — SQLite | Як в етапі 1: SQLite-форма з `.claude/rules/migrations.md` § Repo adaptation; `TEXT` + межі в Pydantic (`filament_name` ≤ 200 code points, `filament_color` `^#[0-9A-F]{6}$`) |
| 2 | Межу довжини назви пресету SAD §8 віддав data-model, а джерела в PRD немає | **200 code points** — з запасом над еталоном (24 символи) і над користувацькими пресетами Bambu. Довша назва з файлу → «файл пошкоджений» (SAD §8), тож мовчазного обрізання не буває. Перевизначити, якщо реальний пресет виявиться довшим |
| 3 | Змінна сутність (upsert), а `updated_at` немає | Immutable-first (дефолт курсу): PRD не вимагає часу зміни, перегляду зіставлень немає (PRD §3). **Винесено на рішення автора** — додати `updated_at` можна пізніше окремою міграцією |
| 4 | Сурогатний UUIDv7 `id` поряд із природним ключем | Вимога SAD §8 ID strategy; природний ключ тримає UNIQUE. Альтернатива — складений PK `(filament_name, filament_color)` без `id`, як `item_plastics` |
| 5 | `CLAUDE.md` § Money/units не знає суфікса `*_mg` | У БД `*_mg` немає (лише у відповіді розбору, ADR 0004). Борг SAD §11 лишається для `CLAUDE.md`, на схему він не впливає |
| 6 | `docs/architecture-map.md` застарів (`reflects_commit: 95f8e06`) | Локацію міграцій і інструмент узято з `CLAUDE.md` і live-дерева; вони збігаються з картою. Борг SAD §11: запустити `/sdlc:map-architecture` до `/sdlc:break-tasks` |

**Promote-time hints для `implement-tasks`:**
- 3 твердження в `upgrade()` і 3 в `downgrade()` — кожне окремим `op.execute("""…""")`.
- `down_revision` — head на момент promote (зараз `65f15a51514f`).
- `importing/tables.py` дзеркалить SQL: `ForeignKey("plastics.id", ondelete="CASCADE")`, `Index("uq_filament_mappings_name_color", …, unique=True)`, `Index("idx_filament_mappings_plastic_id", "plastic_id")`.
- Upsert — `sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_update(index_elements=["filament_name", "filament_color"], set_={"plastic_id": stmt.excluded.plastic_id})`. `id` для нових рядків генерує `new_id()` ще до виклику: при конфлікті його просто відкидають.
- `IntegrityError` FOREIGN KEY під час upsert → repo-виняток → доменна помилка; вся транзакція виробу відкочується (ADR 0003). Код помилки фіксує `api-forge` (SAD §6 flag до потоку 6).
- Варто додати в `tests/integration/test_migrations.py` перевірку, що після head таблиця `filament_mappings` є, а після downgrade на одну ревізію її немає.

## Drift findings

**Schema-vs-source:** для нової таблиці пропущено, бо модуля `backend/src/calculate3d/modules/importing/` ще немає, і `_drift/` не створено. Наявні `pricing/tables.py` (`plastics.id TEXT PK`) і `catalog` фіча не змінює. FK-ціль `plastics(id)` існує в коді й у live-міграції `20261028_2230`.

**Model-vs-spec:**

| PRD / SAD entity | Table | Status |
|---|---|---|
| зіставлення пластиків (US-03; AC-07..AC-11; SAD §5 `importing/tables.py`; ADR 0003, 0005) | `filament_mappings` | ✓ |
| FK на пластик з ON DELETE CASCADE (AC-11; ADR 0003) | `filament_mappings.plastic_id` | ✓ |
| унікальність (назва, колір) (SAD §5; AC-09, AC-10) | `uq_filament_mappings_name_color` | ✓ |
| виріб / витрата пластику / час друку (AC-01, AC-05) | `items`, `item_plastics` етапу 1 | ✓ без змін |
| файл слайсера, розібрані філаменти, `usage_mg`, пластина | — | ✓ навмисно не зберігається (ADR 0001, PRD §6) |
| «було → стало», незавершений імпорт (AC-05, AC-09b) | — | ✓ лише стан форми вебу (SAD §5) |
| тип філамента (AC-07 «назва, тип, колір») | — | ✓ показується з файлу, у ключ зіставлення не входить (CONTEXT, AC-09) |

Таблиць без походження в PRD/SAD немає. У SAD немає окремого розділу «§6.4 ER». ER-заготовкою слугували коментар `tables.py` у SAD §5, ADR 0003 і нотатки `persists …` у потоці 6, і їх виконано повністю.

## Breaking changes decomposed

Немає: лише `CREATE` нової таблиці. Наявні таблиці не змінюються, тож expand → backfill → contract не потрібен.

## Seeds

Немає (bootstrap / lookup не потрібні). Тестову фабрику `make_filament_mapping` описано в `data-model.md` § Test fixtures. Код відкладено до `implement-tasks`.

## TBDs

Немає: `data-model.md` не містить `<!-- TBD -->`. Відкриті рішення автора, а не TBD: divergence №2 (межа 200) і №3 (`updated_at`).
