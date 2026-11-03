## Summary

Етап 1 калькулятора собівартості 3D-друку. Сервер рахує мінімальний донат у гривнях
(пластик + електрика + знос + брак) із введених вручну грамів і часу друку. Розрахунок можна
зберегти як виріб у каталозі, і ціна виробу щоразу перераховується з поточних налаштувань.
Контекст і цілі: [PRD](docs/features/cost-calculator/PRD.md).

## Acceptance criteria

- AC-01: пластик додано з ціною за кг, десяткову частину можна вводити через кому або крапку ✓
- AC-02: порожню назву, назву >100 символів, повтор назви (без урахування регістру, після trim) і хибну ціну відхилено ✓
- AC-03: пластик, який використовує виріб, не видаляється, і відповідь називає ці вироби ✓
- AC-04: налаштування зберігаються однією дією, знос 7,00 ₴/год ✓
- AC-05: будь-яке хибне поле блокує збереження всієї форми, межі й точність названо ✓
- AC-06 / AC-06b: 115,25 ₴ (78,00 / 2,27 / 24,50 / 10,48) і 80,63 ₴ (пластик 58,00), перерахунок автоматичний ✓
- AC-07: хибні витрата, час, ліміти й повтор пластику блокують ціну та збереження ✓
- AC-08 / AC-08b: донат округлюється вгору з точної суми, 96,74 ₴ при сумі рядків 96,73 ₴ ✓
- AC-09: без налаштувань розрахунок блокується з переліком того, чого бракує ✓
- AC-10 / AC-11: виріб зберігає параметри без ціни, а назва перевіряється на унікальність і довжину ✓
- AC-12: пошук за частиною назви, порядок латиниця → українська абетка ✓
- AC-13: після зміни ціни PETG на 800 ₴/кг донат стає 135,05 ₴ без жодних дій з виробом ✓
- AC-14 / AC-14b / AC-14c: перегляд, редагування з перерахунком, невалідну зміну відхилено ✓
- AC-15: виріб видаляється після підтвердження, і його пластики знову можна видалити ✓
- AC-16: сервер слухає лише 127.0.0.1 ✓
- AC-16b: чужий `Host` (DNS rebinding), cross-origin запити та не-JSON запити, що змінюють дані, відхиляються ✓

## Design

- PRD: `docs/features/cost-calculator/PRD.md`
- Architecture: `docs/features/cost-calculator/sad.md`
- Decisions: `docs/features/cost-calculator/adr/` (0001–0007)
- Data model + migration: `docs/features/cost-calculator/data-model.md` (4 Alembic-ревізії `20261028_2230…2233`)
- API: `docs/features/cost-calculator/contracts/openapi.yaml` (`api-sync-report.md`: PASS (with deferrals))
- Test plan: `docs/features/cost-calculator/test-plan.md`
- Reviews: `docs/features/cost-calculator/_review/`, 6 раундів, останній `review-2026-11-03.md`: **PASS**
- Changelog: `docs/features/cost-calculator/CHANGELOG.md`

## Tasks (SDLC-Task trailers)

<details><summary>49 task commits (з 78 комітів гілки)</summary>

- `fe40131` feat(cost-calculator): promote staged migrations into the Alembic chain — T1
- `9f6225b` feat(cost-calculator): add core/text name rules and problem+json extension members — T2
- `223a6a6` feat(cost-calculator): guard the local API with Host allowlist, same-origin and JSON-only checks — T3
- `0c68494` feat(cost-calculator): serve index.html for client-side routes (SPA fallback) — T4
- `7a1ca0f` feat(cost-calculator): add the pure cost formula with an exact reference table — T5
- `9bda652` feat(cost-calculator): add React Router shell, parse-decimal and format-money — T13
- `450c1e7` feat(cost-calculator): add the pricing module (plastics + price settings) and per-test DBs — T6
- `54bacde` feat(cost-calculator): expose /api/pricing (plastics CRUD + price settings) — T7
- `4e6494d` feat(cost-calculator): price a print via costing.service and POST /api/costing/quote — T8
- `384ba2c` feat(cost-calculator): add catalog tables and repo with batch reads — T9
- `bd601a3` feat(cost-calculator): add catalog.service (save, edit, delete, search, live prices) — T10
- `7ee38ef` feat(cost-calculator): expose /api/catalog/items and wire the plastic-in-use check — T11
- `b30e372` test(cost-calculator): add NFR, contract, golden-path and guard-state tests — T12
- `9478569` feat(cost-calculator): manage plastics on /settings (list, add, edit, delete) — T14
- `9f48621` feat(cost-calculator): edit the six price settings on /settings in one save — T15
- `97c0bf4` feat(cost-calculator): add the debounced quote entity and the cost-breakdown widget — T16
- `05984bb` feat(cost-calculator): build /calculate with the live quote form — T17
- `59b3f0c` feat(cost-calculator): save the shown calculation to the catalog from /calculate — T18
- `e949460` feat(cost-calculator): build /catalog with ?q= search and live minimum donations — T19
- `d11bbcf` feat(cost-calculator): build /catalog/:itemId — view, edit with a live quote, delete — T20
- `fe511cc` fix(cost-calculator): expose costing DTOs via service.py and point duplicate-plastic 422 at the field — T21
- `32ca2d8` fix(cost-calculator): refuse to save a catalog item that cannot be priced (AC-10 on the server) — T22
- `8f2db45` fix(cost-calculator): make the live OpenAPI match the contract schema by schema — T23
- `ac2b590` fix(cost-calculator): cap scaled-integer inputs and normalise names (NFC, edge format chars) — T24
- `f4c4af3` fix(cost-calculator): serialize check-then-write with BEGIN IMMEDIATE and translate FK violations — T25
- `f2634e6` test(cost-calculator): cover the plastic edit path of AC-02 at API and UI level — T26
- `ed69249` fix(cost-calculator): never show a donation priced from old plastics or settings — T27
- `73dd2da` fix(cost-calculator): type problem extensions from the schema and explain quote errors on both screens — T28
- `97fe124` docs(cost-calculator): record exact Fraction intermediates with Decimal rounding (ADR 0004 amendment) — T30
- `a97197a` fix(cost-calculator): describe hours/minutes errors to assistive tech and tighten quote tests — T29
- `4cb4f74` docs(cost-calculator): align the SAD with the Fraction amendment, restore ADR 0004 links, refresh the duplicate-plastic example — T36
- `49cefd7` fix(cost-calculator): emit format: uuid on id path parameters and make their contract test non-vacuous — T31
- `8f04b52` fix(cost-calculator): wrap a failed BEGIN IMMEDIATE as a SQLAlchemy error and keep the health ping lock-free — T32
- `982dcb9` fix(cost-calculator): measure name length after NFC so an expanding name is a 422, not a 500 — T33
- `3ff9a34` test(cost-calculator): assert a quote saves nothing and a blank-name edit is rejected — T37
- `407861d` fix(cost-calculator): state the input caps in the PRD and explain them next to the field — T34
- `36c7505` fix(cost-calculator): never show an empty state over the previous search's placeholder rows — T35
- `b2bea2f` fix(cost-calculator): name the limit for an oversized number and state range with precision — T39
- `fff7a56` test(cost-calculator): reject over-cap values on the settings, calculate and item screens — T40
- `cadada1` fix(cost-calculator): count name length as the server does and await the catalog reload in its test — T41
- `6d3116a` docs(cost-calculator): trace the input caps in the test plan and reconcile the contract — T38
- `ff958eb` test(cost-calculator): pin every input cap at the boundary and the 32-plastic limit end to end — T42
- `a9c5568` fix(cost-calculator): trim names on the web exactly as the server does — T44
- `57db160` fix(cost-calculator): explain bad minutes alone and keep each cap message in one place — T45
- `a4cbab2` docs(cost-calculator): name the 100-character name cap and the quote caps across PRD, SAD and contract — T43
- `873ae1a` test(cost-calculator): pin the 100-character name cap on the server with emoji and edge Cf — T46
- `68d23bb` test(cost-calculator): show the name cap on every form and prove the 32-plastic cap alone blocks a quote — T47
- `5d2e33c` fix(cost-calculator): trim names in linear time and state the price cap once — T48
- `7aed98f` docs(cost-calculator): carry the 100-character name cap into the SAD flows, AC-14c and the item 422 — T49

</details>

## Verification

- Unit + integration: `make check` на `3e332a5` пройшов. Backend `pytest`: 375 passed / 4 skipped (прийняті named-schema кейси `test_contract.py`), інтеграційні тести працюють з реальною SQLite після Alembic. Web `vitest`: 283 passed.
- Lint + types: `ruff check` / `ruff format --check` / `mypy --strict`, ESLint + Prettier + Steiger, `tsc -b`, `vite build` і `api-types-check` чисті.
- Ran the feature: застосунок запущено через `make run` (міграції, збірка UI, один процес на `127.0.0.1:8000`) з окремою свіжою БД, AC перевірено через HTTP:
  - AC-09: до налаштування `409 costing.settings_missing`, `missing: [plastics, price_settings]`.
  - AC-04, AC-06, AC-06b, AC-08b: `wear_per_hour_kop 700`, донати `11525`, `8063` і `9674`, розбивки збігаються з PRD.
  - AC-02, AC-11: `petg чорний ` і `брелок-тризуб` отримали `409 *.name_taken`.
  - AC-07: повтор пластику дав `422`.
  - AC-03: `409 pricing.plastic_in_use` з `items: ["Брелок-тризуб"]`.
  - AC-13: після зміни ціни PETG на 800 ₴/кг каталог і картка виробу показують `13505`.
  - AC-12: пошук `?q=тризуб` працює, порядок `Benchy, гачок, ґудзик, єдиноріг, Іграшка, Ялинка`.
  - AC-14c: `print_time_s: 0` дав `422`.
  - AC-15: виріб видалено (`204`), після цього пластик теж видаляється (`204`).
  - AC-16: сокет слухає лише `127.0.0.1:8000`, з LAN-адреси з'єднання не встановлюється.
  - AC-16b: чужий `Host` дав `400 host_not_allowed`, чужий `Origin` на PUT і `Sec-Fetch-Site: cross-site` на GET дали `403`, `text/plain` POST дав `415`, налаштування після цього не змінились.
  - SPA: `/` і `/catalog` віддають `index.html`.
- UI у живому браузері: `/sdlc:verify-ui` (Chromium через `playwright-cli`, `make run`) проходить 20 з 20 UI-перевірних AC (AC-16/16b не відтворюються в UI, їх закрито HTTP-прогоном вище). Вердикти й скріншоти лежать у `docs/features/cost-calculator/_review/verify-ui-2026-11-03.md`.

## Operational notes

- Migration: 4 нові ревізії, `make run` / `make migrate` застосовують їх автоматично. Rollback: `make migrate-down` ×4 (дані фічі видаляються, тому спершу варто скопіювати `backend/var/calculate3d.db`) і revert.
- Feature flag / config: немає. `CALC3D_DATABASE_URL` як і раніше, bind лише `127.0.0.1`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
