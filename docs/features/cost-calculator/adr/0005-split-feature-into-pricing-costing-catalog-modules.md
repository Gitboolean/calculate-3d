---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-28"
feature_size: M
stage: "04-05"
ticket: ""
---

# 0005 — Split the feature into pricing, costing and catalog modules; pricing gets item usage by parameter

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Anton Pohorielov (автор), architecture-design pass

## Context

Скаффолд має лише модуль `health`; доменні модулі проєктує ця фіча (architecture-map, «Module inventory»). У глосарії три окремі поняття: **налаштування цін** (пластики + тариф, потужність, знос, брак), **розрахунок** (живе лише на екрані, не зберігається) і **каталог** (вироби з витратою пластиків). Проєктний ADR 0002 дозволяє модулям звертатися один до одного лише через `service.py`. AC-03 вимагає, щоб видалення пластику, який використовує хоча б один виріб, відхилялося з переліком цих виробів, а знає про вироби лише каталог.

## Decision drivers

- Проєктний ADR 0002: модульний моноліт, router → service → repo, міжмодульно — лише `service.py`.
- QG-1 Точність: формула ізольована від I/O і покрита еталонною таблицею (ADR 0002 фічі).
- ADR 0003 фічі: каталог викликає ту саму функцію розрахунку, що й ендпоінт розрахунку.
- Етап 2 (імпорт файлу слайсера) має додатися без перекроювання наявних модулів (PRD §3).

## Considered options

1. **Три модулі `pricing` / `costing` / `catalog`** — `costing` без таблиць (чиста формула + ендпоінт розрахунку); залежності `catalog → costing → pricing`; для AC-03 `pricing` отримує пошук виробів як параметр.
2. **Два модулі `pricing` + `catalog`** — формула і ендпоінт розрахунку всередині `pricing`; менше міжмодульних викликів, але розрахунок ховається в налаштуваннях.
3. **Один модуль `calculator`** — без міжмодульних правил, але без демонстрації модульного моноліту; на етапі 2 його доведеться ділити.

## Decision outcome

**Chosen:** Option 1.

- `modules/pricing/` — пластики (CRUD) і налаштування цін (одна форма, один рядок); префікс `/api/pricing`. Віддає поточні ціни через `service.py`.
- `modules/costing/` — `domain.py` з чистою формулою на `Decimal` (без I/O), `service.py` бере поточні ціни з `pricing.service` і рахує розрахунок; префікс `/api/costing`; `repo.py`/`tables.py` немає, бо розрахунок не зберігається.
- `modules/catalog/` — вироби та їхня витрата пластиків; префікс `/api/catalog`; ціни — через `costing.service` (ADR 0003). Посилання рядка витрати на пластик — FK з `ON DELETE RESTRICT`.
- **AC-03 без циклу залежностей:** `pricing.service.delete_plastic(conn, plastic_id, used_by)` приймає функцію `used_by(conn, plastic_id) -> list[str]`, а підставляє `catalog.service.item_names_using_plastic` **роутер** `pricing`. Сервіс `pricing` про каталог не знає. FK `RESTRICT` — друга лінія захисту інваріанту, якщо перевірку колись оминуть.

## Consequences

**Positive**
- Формула тестується без БД і HTTP; і розрахунок, і каталог викликають її через `costing.service`.
- Межі збігаються з глосарієм (налаштування цін / розрахунок / каталог), тож зрозуміло, куди класти новий код.
- Імпорт етапу 2 може стати окремим модулем, що лише заповнює вхід розрахунку.

**Negative**
- Роутер `pricing` імпортує `catalog.service` — єдине місце, де залежність іде «вгору»; це треба пояснити коментарем, щоб ніхто не «виправив» це прямим імпортом у сервісі.
- Три модулі = три роутери, три набори схем і більше файлів, ніж у варіанті з одним модулем.

**Neutral**
- Злиття `costing` у `pricing` пізніше змінить лише префікс URL і згенеровані типи вебу.

## Links

- PRD: [[../PRD.md]] AC-03, AC-06, AC-13; §3 (етап 2)
- SAD: [[../sad.md]] §5
- Project ADR: [[../../../adr/0002-organize-as-modular-monolith-with-simple-layers.md]]
- Related ADR: [[0002-compute-cost-on-server-only]], [[0003-recompute-catalog-prices-on-every-read]]
