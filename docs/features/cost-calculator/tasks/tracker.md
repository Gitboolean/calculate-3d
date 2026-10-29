# Tracker — cost-calculator

> Status of every task in the epic. `implement-tasks` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`.
> Estimate: S = 2 год · M = пів дня · L = день.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| [T1](./T1-promote-migrations.md) | Перенести 4 staged-міграції в ланцюжок Alembic і задокументувати суфікси одиниць | migration | Anton Pohorielov | S | — | done |
| [T2](./T2-core-names-and-problem-extensions.md) | Додати core/text.py (trim, name_key, пошук, український порядок) і поля-розширення AppError | domain | Anton Pohorielov | M | — | done |
| [T3](./T3-request-guard.md) | Додати middleware захисту запитів: allowlist Host, same-origin, JSON-only | wiring | Anton Pohorielov | M | — | done |
| [T4](./T4-spa-fallback.md) | Віддавати index.html для будь-якого не-/api шляху (SPA fallback) | wiring | Anton Pohorielov | S | — | done |
| [T5](./T5-costing-domain-formula.md) | Реалізувати чисту формулу собівартості costing.domain на Decimal з еталонною таблицею | domain | Anton Pohorielov | M | — | done |
| [T6](./T6-pricing-service.md) | Зібрати модуль pricing: tables, repo, service, schemas для пластиків і налаштувань цін | app | Anton Pohorielov | L | T1, T2, T5 | done |
| [T7](./T7-pricing-router.md) | Відкрити /api/pricing: CRUD пластиків і GET/PUT налаштувань цін | ports | Anton Pohorielov | M | T6 | done |
| [T8](./T8-costing-quote-endpoint.md) | Реалізувати costing.service.quote() і POST /api/costing/quote | ports | Anton Pohorielov | M | T5, T7 | done |
| [T9](./T9-catalog-repo.md) | Додати catalog tables + repo: вироби з рядками витрати, пакетне читання без N+1 | infra | Anton Pohorielov | M | T1 | done |
| [T10](./T10-catalog-service.md) | Реалізувати catalog.service: збереження, редагування, видалення, пошук і перерахунок цін | app | Anton Pohorielov | L | T2, T8, T9 | done |
| [T11](./T11-catalog-router-and-plastic-in-use.md) | Відкрити /api/catalog/items і підключити перевірку використання пластику в pricing (AC-03) | ports | Anton Pohorielov | L | T7, T8, T10 | done |
| [T12](./T12-nfr-and-contract-tests.md) | Додати тести NFR (латентність, збереженість, узгодженість цін) і контрактний тест OpenAPI | tests | Anton Pohorielov | M | T3, T11 | done |
| [T13](./T13-web-foundation.md) | Підключити React Router, оболонку з навігацією, parse-decimal і format-money | ui | Anton Pohorielov | M | — | done |
| [T14](./T14-settings-plastics-ui.md) | Зібрати розділ пластиків на /settings: список, додавання, редагування, видалення з підтвердженням | ui | Anton Pohorielov | L | T7, T13 | done |
| [T15](./T15-settings-price-form-ui.md) | Зібрати форму налаштувань цін на /settings: 6 полів, одне збереження, знос за годину | ui | Anton Pohorielov | M | T7, T13, T14 | done |
| [T16](./T16-quote-entity-and-breakdown-widget.md) | Додати entity quote (debounce + ключ запиту) і віджет cost-breakdown | ui | Anton Pohorielov | M | T8, T13 | done |
| [T17](./T17-calculate-page-quote-form.md) | Зібрати сторінку /calculate з формою quote-form, валідацією AC-07 і станом «бракує налаштувань» | ui | Anton Pohorielov | L | T14, T16 | done |
| [T18](./T18-save-item-ui.md) | Додати збереження розрахунку в каталог (feature save-item) на /calculate | ui | Anton Pohorielov | M | T11, T17 | done |
| [T19](./T19-catalog-page-ui.md) | Зібрати сторінку /catalog: пошук за ?q= і список виробів з актуальним мінімальним донатом | ui | Anton Pohorielov | M | T11, T13, T18 | done |
| [T20](./T20-item-page-ui.md) | Зібрати сторінку /catalog/:itemId: перегляд, редагування через quote-form і видалення | ui | Anton Pohorielov | L | T17, T18 | done |
| [T21](./T21-costing-dto-and-duplicate-loc.md) | Відкрити DTO costing через service.py і повертати loc поля для дубля пластику | app | Anton Pohorielov | S | — | done |
| [T22](./T22-server-side-ac10.md) | Перевіряти на сервері, що виріб має ціну, перед збереженням (AC-10) | app | Anton Pohorielov | S | T21 | done |
| [T23](./T23-openapi-schema-fidelity.md) | Звести живий OpenAPI з контрактом на рівні схем і задекларувати 415 на DELETE | ports | Anton Pohorielov | S | T22 | done |
| [T24](./T24-input-bounds-and-names.md) | Обмежити масштабовані цілі зверху і нормалізувати імена (NFC, невидимі символи) | app | Anton Pohorielov | S | T23 | done |
| [T25](./T25-tx-serialization-fk.md) | Серіалізувати перевірку і запис у транзакції та перекладати FK IntegrityError у доменні помилки | infra | Anton Pohorielov | S | T22 | done |
| [T26](./T26-ac02-edit-tests.md) | Покрити шлях редагування пластику з AC-02 integration- і UI-тестами | tests | Anton Pohorielov | S | T24 | done |
| [T27](./T27-web-cache-freshness.md) | Не показувати донат за старими цінами з кешу і не блимати списком під час пошуку | ui | Anton Pohorielov | S | — | done |
| [T28](./T28-web-problem-types-and-quote-errors.md) | Типізувати problem-розширення зі згенерованих схем і показувати помилки quote на обох екранах | ui | Anton Pohorielov | S | T23, T27 | done |
| [T29](./T29-a11y-and-test-tightening.md) | Зв'язати помилки годин/хвилин через aria-describedby і посилити тести AC-14b та моки quote | ui | Anton Pohorielov | S | T28 | done |
| [T30](./T30-fraction-adr-amendment.md) | Задокументувати точні Fraction-проміжні обчислення в ADR 0004 і CLAUDE.md | docs | Anton Pohorielov | S | — | done |
| [T31](./T31-path-param-uuid-format.md) | Типізувати id у path-параметрах як Id (format: uuid) і полагодити контрактний тест параметрів | ports | Anton Pohorielov | S | — | done |
| [T32](./T32-tx-begin-wrapped-and-health.md) | Брати BEGIN IMMEDIATE через SQLAlchemy і не блокувати health-ping | infra | Anton Pohorielov | S | — | done |
| [T33](./T33-nfc-before-length.md) | Нормалізувати ім'я (NFC) до перевірки довжини, щоб довге після NFC ім'я давало 422 | app | Anton Pohorielov | S | — | done |
| [T34](./T34-caps-in-prd-and-ui.md) | Записати верхні межі в PRD і пояснювати їх біля поля в UI | ui | Anton Pohorielov | S | T33 | done |
| [T35](./T35-web-settings-evict-test-and-empty-state.md) | Покрити тестом скидання кешу цін після налаштувань і не показувати порожній стан поверх placeholder-даних | ui | Anton Pohorielov | S | — | done |
| [T36](./T36-docs-fraction-sad-links-example.md) | Узгодити SAD з поправкою ADR 0004, повернути ## Links і оновити приклад msg у контракті | docs | Anton Pohorielov | S | — | done |
| [T37](./T37-test-plan-literal-asserts.md) | Дописати асерти test-plan: quote не створює виріб, порожня назва при редагуванні не зберігається | tests | Anton Pohorielov | S | — | done |

**Total:** 37 tasks (20 + 17 review follow-ups), ~14.6 person-days (117 год).
