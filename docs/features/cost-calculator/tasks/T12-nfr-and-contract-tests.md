---
id: T12
title: "Додати тести NFR (латентність, збереженість, узгодженість цін) і контрактний тест OpenAPI"
layer: "tests"
deps: ["T3", "T11"]
acs: ["AC-01", "AC-03", "AC-04", "AC-06", "AC-10", "AC-12", "AC-13", "AC-15", "AC-16b"]
files_hint: ["backend/tests/integration/test_nfr_latency.py", "backend/tests/integration/test_nfr_durability.py", "backend/tests/integration/test_price_consistency.py", "backend/tests/integration/test_contract.py", "backend/tests/integration/test_e2e_golden_path.py", "backend/tests/integration/test_request_guard.py", "backend/pyproject.toml", "backend/uv.lock"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T12 — Додати тести NFR (латентність, збереженість, узгодженість цін) і контрактний тест OpenAPI

## Why

[sad.md](../sad.md) §10 QG-1 (3), QG-2, QG-3 (b–d, «стан БД незмінний»), QG-4; [api-sync-report.md](../contracts/api-sync-report.md) § D (дифф `/openapi.json` ↔ контракт; реєстр 13 кодів помилок). [test-plan.md](../test-plan.md) § E2E (API), § NFR validation. Критерії: AC-01, AC-03, AC-04, AC-06, AC-10, AC-12, AC-13, AC-15, AC-16b у [PRD §5](../PRD.md).

## What

- QG-2: p95 `POST /api/costing/quote` ≤ 300 мс і `GET /api/catalog/items` ≤ 500 мс на `seed_catalog_volume(1000, 50)`; прогрів + ≥ 50 вимірів; `pytest.mark.skipif(os.environ.get("CI"))`.
- Без N+1 (не залежить від `CI`, працює і в CI): кількість SQL-запитів на один `GET /api/catalog/items` однакова для 10 і для 1 000 виробів. Рахувати через `sqlalchemy.event.listen(Engine, "before_cursor_execute", …)` на час одного запиту; після тесту знімати слухач.
- QG-4: зберегти налаштування, пластик і виріб → `engine.dispose()` → новий `create_app()` на тому самому файлі → усі поля збігаються.
- QG-1 (3): для тих самих параметрів `quote` і `listItems`/`getItem` дають однаковий `min_donation_kop`.
- QG-3: для кожної змінної операції — запит з чужим `Origin` / не-JSON → відмова, і стан БД не змінився.
- E2E (API), «золотий шлях» з test-plan: один тест на власному файлі БД — `PUT` налаштувань AC-04 → пластик «PETG чорний» 650 ₴/кг → `quote` = 115,25 ₴ (11525 коп) → зберегти «Брелок-тризуб» → каталог 11525 → видалити пластик не можна (AC-03, виріб названо) → ціна 800 ₴/кг → каталог 13505 → видалити виріб → пластик видаляється (AC-15).
- Контракт: шляхи, операції й коди error-відповідей у `app.openapi()` ⊇ `contracts/openapi.yaml`; набір `code` з `AppError`-підкласів = 13 кодів контракту. Додати dev-залежність `pyyaml` (+ `types-PyYAML`).

## Definition of Done

- [ ] Латентність: p95 у межах на машині автора; при `CI=1` — skip з поясненням.
- [ ] Збереженість, узгодженість цін і guard-тести «стан незмінний» — зелені.
- [ ] Тест «без N+1» зелений і в CI; падає, якщо замінити пакетне читання рядків витрати на читання по одному виробу (перевірено вручну один раз).
- [ ] Наскрізний сценарій API зелений; кожен крок перевіряє суму в копійках, а не лише статус.
- [ ] Контрактний тест падає, якщо прибрати будь-яку `responses=` з роутера (перевірено вручну один раз).
- [ ] `make check` зелений.

## Notes

- **Blocked by:** [T3](./T3-request-guard.md), [T11](./T11-catalog-router-and-plastic-in-use.md).
- Закриває deferrals 2 і 3 з api-sync-report.
- Тести, що пишуть у БД (наскрізний сценарій, збереженість, латентність), працюють на власному файлі БД, а не на спільному сесійному `engine` (test-plan § Test data).
- Ручний чеклист перед релізом (test-plan § Manual pre-release checklist) — не частина цієї задачі; його проходять на `/sdlc:ship-feature`.
