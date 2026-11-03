# Changelog — cost-calculator

## cost-calculator — мінімальний донат 3D-друку з розбивкою собівартості та каталог з актуальною ціною

**What:** інструмент тепер рахує собівартість друку, тобто мінімальний донат у гривнях. Автор
веде в налаштуваннях цін список пластиків із ціною за кілограм, а також тариф на електрику,
потужність принтера, знос (ціна принтера, термін служби, деталі за годину) і відсоток браку.
Далі він вводить витрату кожного пластику в грамах і час друку зі слайсера, і розрахунок
одразу показує мінімальний донат із розбивкою: пластик, електрика, знос, брак. Розрахунок можна
зберегти як виріб у каталозі. Каталог шукає за частиною назви, сортує за українською абеткою і
щоразу перераховує ціну кожного виробу з поточних налаштувань. Вироби можна відкривати,
змінювати й видаляти. Пластик, який використовує хоча б один виріб, видалити не можна.

**Why:** автор продає вироби за донат на ЗСУ і досі ставив ціну «на око», тож частина продажів
могла непомітно йти в мінус ([PRD](./PRD.md) §1–§2). Ключові рішення:

- [ADR-0002](./adr/0002-compute-cost-on-server-only.md): формулу рахує лише сервер, тож UI не
  може розійтися з еталонною таблицею.
- [ADR-0003](./adr/0003-recompute-catalog-prices-on-every-read.md): каталог зберігає параметри,
  а не ціну, і перераховує її при кожному читанні (AC-13).
- [ADR-0004](./adr/0004-exchange-quantities-as-scaled-integers.md): усі дробові величини
  передаються як масштабовані цілі (`*_kop`, `*_cg`, `*_permille`, `*_s`). Проміжні значення
  рахуються точно через `Fraction`, а донат округлюється вгору до копійки.
- [ADR-0005](./adr/0005-split-feature-into-pricing-costing-catalog-modules.md): три модулі
  `pricing` · `costing` · `catalog`.
- [ADR-0006](./adr/0006-enforce-name-uniqueness-via-casefolded-name-key.md): унікальність назв
  не залежить від регістру (через casefold-ключ), назви нормалізуються (NFC, обрізаються
  пробіли й невидимі символи на краях) і мають не більше 100 символів.
- [ADR-0007](./adr/0007-guard-local-api-with-host-allowlist-and-same-origin-checks.md): API
  захищено allowlist для `Host`, перевірками same-origin і JSON-only від сторонніх сайтів і
  DNS rebinding (AC-16b).

**How to use:** `make run` → <http://127.0.0.1:8000>. Порядок: налаштування цін, потім
розрахунок, потім «Зберегти в каталог». API описано в [openapi.yaml](./contracts/openapi.yaml):

```http
POST /api/costing/quote
{"plastics":[{"plastic_id":"<id PETG чорний>","usage_cg":12000}],"print_time_s":12600}
→ 200 {"min_donation_kop":11525,"breakdown":{"plastic_kop":7800,"electricity_kop":227,"wear_kop":2450,"scrap_kop":1048}}
```

Інші ендпоінти: `/api/pricing/plastics[/{id}]`, `/api/pricing/settings`,
`/api/catalog/items[/{id}]` (`?q=` для пошуку). Кожна помилка повертається як RFC 9457
`application/problem+json` з `code` (`pricing.name_taken`, `pricing.plastic_in_use`,
`costing.settings_missing`, `catalog.name_taken`, `validation_error`, …).

**Operational notes:**

- Migration: 4 нові Alembic-ревізії (`20261028_2230_create_plastics`, `…_2231_create_price_settings`,
  `…_2232_create_items`, `…_2233_create_item_plastics`), перенесені зі staged
  [`migrations/`](./migrations/). `make run` запускає `make migrate` сам. Окремо міграцію можна
  виконати через `make migrate`. Цикл upgrade → downgrade → upgrade перевірено тестом.
- Feature flag / config: немає. Шлях до БД, як і раніше, задає `CALC3D_DATABASE_URL`. Сервер
  слухає лише `127.0.0.1` (ADR 0004 проєкту).
- Rollback: зупинити сервер, виконати `make migrate-down` 4 рази (таблиці `item_plastics` →
  `items` → `price_settings` → `plastics` видаляються разом із даними), потім revert мерджу.
  Перед відкатом варто скопіювати `backend/var/calculate3d.db`.

**Acceptance criteria delivered:** AC-01 … AC-16b, усього 21 AC ([PRD](./PRD.md) §5). Пластики
з ціною й валідацією (AC-01–03), налаштування тарифу, зносу й браку однією дією (AC-04–05),
миттєвий розрахунок із точністю до копійки та округленням донату вгору (AC-06–09), каталог зі
збереженням, пошуком, абетковим сортуванням і ціною за поточними налаштуваннями (AC-10–15),
доступ лише з комп'ютера автора і захист від сторонніх сайтів (AC-16, AC-16b).
