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
| [T12](./T12-nfr-and-contract-tests.md) | Додати тести NFR (латентність, збереженість, узгодженість цін) і контрактний тест OpenAPI | tests | Anton Pohorielov | M | T3, T11 | todo |
| [T13](./T13-web-foundation.md) | Підключити React Router, оболонку з навігацією, parse-decimal і format-money | ui | Anton Pohorielov | M | — | done |
| [T14](./T14-settings-plastics-ui.md) | Зібрати розділ пластиків на /settings: список, додавання, редагування, видалення з підтвердженням | ui | Anton Pohorielov | L | T7, T13 | todo |
| [T15](./T15-settings-price-form-ui.md) | Зібрати форму налаштувань цін на /settings: 6 полів, одне збереження, знос за годину | ui | Anton Pohorielov | M | T7, T13, T14 | todo |
| [T16](./T16-quote-entity-and-breakdown-widget.md) | Додати entity quote (debounce + ключ запиту) і віджет cost-breakdown | ui | Anton Pohorielov | M | T8, T13 | todo |
| [T17](./T17-calculate-page-quote-form.md) | Зібрати сторінку /calculate з формою quote-form, валідацією AC-07 і станом «бракує налаштувань» | ui | Anton Pohorielov | L | T14, T16 | todo |
| [T18](./T18-save-item-ui.md) | Додати збереження розрахунку в каталог (feature save-item) на /calculate | ui | Anton Pohorielov | M | T11, T17 | todo |
| [T19](./T19-catalog-page-ui.md) | Зібрати сторінку /catalog: пошук за ?q= і список виробів з актуальним мінімальним донатом | ui | Anton Pohorielov | M | T11, T13, T18 | todo |
| [T20](./T20-item-page-ui.md) | Зібрати сторінку /catalog/:itemId: перегляд, редагування через quote-form і видалення | ui | Anton Pohorielov | L | T17, T18 | todo |

**Total:** 20 tasks, ~12.5 person-days (100 год).
