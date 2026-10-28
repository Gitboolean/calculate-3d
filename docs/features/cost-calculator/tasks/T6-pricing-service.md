---
id: T6
title: "Зібрати модуль pricing: tables, repo, service, schemas для пластиків і налаштувань цін"
layer: "app"
deps: ["T1", "T2", "T5"]
acs: ["AC-01", "AC-02", "AC-03", "AC-04", "AC-05"]
files_hint: ["backend/src/calculate3d/modules/pricing/__init__.py", "backend/src/calculate3d/modules/pricing/tables.py", "backend/src/calculate3d/modules/pricing/repo.py", "backend/src/calculate3d/modules/pricing/service.py", "backend/src/calculate3d/modules/pricing/schemas.py", "backend/tests/factories.py", "backend/tests/conftest.py", "backend/tests/unit/test_pricing_service.py"]
owner: "Anton Pohorielov"
estimate: "L"
status: "todo"
---

# T6 — Зібрати модуль pricing: tables, repo, service, schemas для пластиків і налаштувань цін

## Why

[sad.md](../sad.md) §5 (модуль `pricing`), §6 «Додати або змінити пластик», «Critical flow 3», «Зберегти налаштування цін»; [data-model.md](../data-model.md) (`plastics`, `price_settings` singleton); [ADR-0005](../adr/0005-split-feature-into-pricing-costing-catalog-modules.md), [ADR-0006](../adr/0006-enforce-name-uniqueness-via-casefolded-name-key.md); схеми — [openapi.yaml](../contracts/openapi.yaml) `PlasticInput`, `Plastic`, `PriceSettingsInput`, `PriceSettings`. Критерії: AC-01, AC-02, AC-03, AC-04, AC-05 у [PRD §5](../PRD.md).

## What

- `tables.py` — `Table`-и на `core.db.metadata`, що дзеркалять міграції T1.
- `repo.py` (бере `Connection`): list/get/insert/update/delete пластику, пошук за `name_key`, `get_settings`, upsert singleton (`INSERT … ON CONFLICT(id) DO UPDATE`, `created_at` не чіпає).
- `service.py`: trim + `name_key`; зайнята назва → `pricing.name_taken` (409, `field=name`); невідомий id → `pricing.plastic_not_found` (404); `delete_plastic(id, item_names_using: Callable[[str], list[str]])` → `pricing.plastic_in_use` (409, `items=[…]`); `get_settings()` → `PriceSettings | None` з `wear_per_hour_kop` (через `core.money.wear_per_hour` з T5); `replace_settings()`; публічні функції для `costing` (`list_plastics_by_ids`, `get_settings`).
- `schemas.py` — Pydantic з `extra="forbid"`, межі з контракту (назва 1–100 після trim, `price_per_kg_kop ≥ 1`, налаштування ≥ 0, `printer_lifetime_h ≥ 1`, `scrap_rate_permille` 0–1000).
- `tests/factories.py`: `make_plastic`, `make_price_settings` (дефолти AC-04).
- `tests/conftest.py` — окремий файл БД для кожного тесту ([test-plan.md](../test-plan.md) § Test data). Зараз `engine` має scope на всю сесію, тож тести pricing і catalog ділили б унікальні назви й singleton налаштувань, і результат залежав би від порядку запуску. Схема: session-фікстура `migrated_db_template` один раз проганяє `alembic upgrade head` у тимчасовий файл; `engine` стає function-scoped — копіює шаблон у `tmp_path` теста, створює `create_db_engine()` і робить `dispose()` після теста. Сигнатура `engine` / `client` не змінюється, тож наявні тести не правимо.

## Definition of Done

- [ ] Unit-тести сервісу (repo підмінено або на SQLite у пам'яті) на AC-01, AC-02 («petg чорний», «PETG чорний »), AC-03 (`items` = назви), AC-04 (знос 700 коп/год), AC-05 (налаштування не очищуються; нуль допустимий).
- [ ] Сервіс не імпортує FastAPI чи SQLAlchemy (лише `repo`).
- [ ] Кожен тест отримує власний файл БД: тест, що пише пластик, не бачить пластика з попереднього теста (перевіряє один тест-«канарка» з двох кроків); наявні тести в `tests/integration/` зелені без змін.
- [ ] `make api-check` зелений.

## Notes

- **Blocked by:** [T1](./T1-promote-migrations.md), [T2](./T2-core-names-and-problem-extensions.md), [T5](./T5-costing-domain-formula.md).
- Сервіс `pricing` **не** імпортує `catalog`: перевірку використання пластику передає параметром роутер (ADR-0005, підключається в T11). Порушення цього правила — Hard rule з sad §5.
- Шаблон копіювати лише після того, як закрито всі з'єднання міграції: `create_db_engine()` вмикає WAL, і незаписані сторінки можуть лишитися в `-wal`-файлі. Або закрити з'єднання з `PRAGMA wal_checkpoint(TRUNCATE)`, або копіювати разом із `-wal`/`-shm`. Інакше копія буде без частини схеми.
- `test_migrations.py` уже працює на власному `tmp_path`-файлі — так і лишити: тест, що робить downgrade, ніколи не бере шаблон чи `engine`.
