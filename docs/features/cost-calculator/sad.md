---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-28"
feature_size: M
stage: "04-05"
ticket: ""
target_surfaces: [backend-service, web-frontend]  # filled in §4 — subset of: backend-service | web-frontend | mobile-app | desktop-app | cli | worker | library-sdk. Read (never re-derived) by api-forge/complete-sequence-diagrams/break-tasks/plan-tests/review-feature → _shared/surfaces.md
---

# Software Architecture Document — cost-calculator

<!-- Stages 04-05 → see sdlc/plugin/skills/architecture-design/SKILL.md -->
<!-- 12 Arc42 sections; an empty section would carry an N/A comment with a one-line reason. -->
<!-- C4 Context (L1) lives inline in §3. C4 Container (L2) lives inline in §5. -->
<!-- §6 Runtime view seeds the primary flow(s) here; complete-sequence-diagrams (stage 06) then -->
<!--    fills §6 with every critical flow / §5 AC — no cap. -->
<!-- Numbers in §10 come VERBATIM from PRD §6 NFR — no inventing, no rounding. -->

## 1. Introduction and goals

**Intent.** Локальний інструмент для **автора**: з **витрати пластику** (по кожному пластику виробу) і часу друку, перенесених зі слайсера, та з поточних **налаштувань цін** він розраховує **мінімальний донат** із **розбивкою собівартості**. **Каталог** зберігає лише параметри **виробу** (не ціну) і щоразу перераховує мінімальний донат з актуальних налаштувань цін, тож повторюваний виріб не продається в мінус непомітно після подорожчання пластику чи тарифу (PRD §2). Цей SAD покриває етап 1 підходу C — ручне введення; імпорт файлу слайсера — окрема фіча (PRD §3).

**Top quality goals (1-liners; full scenarios in §10; порядок = пріоритет при конфлікті):**

1. **QG-1 Точність розрахунку** — 100 % збіг до копійки з еталонною таблицею; мінімальний донат ніколи не менший за собівартість.
2. **QG-2 Чуйність** — перерахунок мінімального донату p95 ≤ 300 мс; відкриття каталогу p95 ≤ 500 мс (1 000 виробів, 50 пластиків).
3. **QG-3 Доступ лише автору** — інструмент недоступний з інших пристроїв і не приймає змін та не віддає даних стороннім сайтам у браузері автора (AC-16, AC-16b).
4. **QG-4 Збереженість** — 100 % збережених змін доступні після перезапуску інструмента чи комп'ютера.

**Stakeholders.**

| Role | Interest | Sign-off owner? |
|---|---|---|
| автор | єдиний користувач (налаштування цін, розрахунок, каталог); водночас власник продукту, архітектор і розробник навчального проєкту | Yes |

**Decision overrides.**

- Decision override: маса пластику — `*_cg` (соті грама, `INTEGER`) замість конвенції `*_g` з `CLAUDE.md` — rationale: точність 0,01 г (AC-07) без `REAL`/float; див. [ADR 0004](adr/0004-exchange-quantities-as-scaled-integers.md), борг оновити `CLAUDE.md` — §11.

## 2. Constraints

**Technical** (версії — з `backend/uv.lock` і `web/package.json` на 2026-10-28).
- Python **3.14** (через `uv`; системний 3.9 не використовується) · FastAPI **0.162** (Starlette 1.10) · Pydantic **2.14** + pydantic-settings 2.16 · Uvicorn 0.54.
- SQLite 3 — один файл, `journal_mode=WAL`, `foreign_keys=ON` на кожному з'єднанні · SQLAlchemy **2.1** Core (без ORM) · Alembic **1.20**, міграції SQL-first (ADR 0003).
- React **19** + TypeScript **5.9** + Vite **8** · Tailwind CSS **4** + shadcn/ui (`web/src/shared/ui/`) · TanStack Query **5** · `openapi-fetch` 0.17 + `openapi-typescript` 7 (типи вебу генеруються з OpenAPI бекенду).
- Модульний моноліт із простими шарами router → service → repo; модулі спілкуються лише через `service.py` іншого модуля (ADR 0002). Веб — Feature-Sliced Design, контроль імпортів — Steiger.
- Один процес, bind лише на `127.0.0.1`, без автентифікації (ADR 0004); без фонових воркерів і багатопроцесних серверів (ADR 0003).

**Organisational.**
- Одна людина: автор — водночас PM, архітектор і розробник.
- Бюджет 2–4 тижні без жорсткого дедлайну (idea-brief §4); навчальний проєкт, який проходить повний SDLC-пайплайн.
- Гейт якості перед кожним комітом і в CI — `make check` (`api-check` + `web-check` + `api-types-check`).

**Conventions.**
- Кореневий `CLAUDE.md` + `backend/CLAUDE.md` + `web/CLAUDE.md` — джерело конвенцій. `docs/architecture-map.md` описує стан до scaffold і застарів (див. §11).
- IDs — UUIDv7 із застосунку (`core/ids.py::new_id()`), `TEXT` 36 символів; БД ID не генерує.
- Гроші — `INTEGER` копійки з суфіксом `_kop`, обчислення — точні `Fraction`, округлення через `decimal.Decimal` (ADR 0004, Amendment 2026-10-29), мінімальний донат округлюється вгору (`ROUND_CEILING`); `float` для грошей заборонено. Одиниця виміру — в назві колонки (`*_s`, `*_w`, `*_per_hour_kop`). **Override (ADR 0004):** маса пластику зберігається цілим числом у сотих грама `*_cg`, а не `*_g` з `CLAUDE.md` (AC-07 вимагає 0,01 г, а `REAL` неточний); частки відсотка — `*_permille`.
- Помилки — `AppError(code, message, status)` → RFC 9457 `application/problem+json`; сервіси не кидають `HTTPException`.
- «БД як тупе сховище»: без CHECK/TRIGGER/бізнес-дефолтів; аудит лише `created_at`; hard delete.
- Каталог зберігає параметри, ніколи не готову ціну.

**Regulatory / external.**
- Персональних даних немає; класифікація даних — internal (PRD §6.1).
- Межа захисту — доступ лише з комп'ютера автора без входу в систему (ADR 0004); потреба в доступі з іншого пристрою — тригер перегляду ADR 0004.
- Abuse cases з PRD §6.1, обов'язкові до виконання: доступ з іншого пристрою в мережі (AC-16), запити сторонніх сайтів у браузері автора, зокрема DNS rebinding (AC-16b), назви, схожі на код чи розмітку (показуються як текст).
- Security review — Required (легкий), фокус: AC-16/AC-16b.

## 3. Context and scope

Автор нарізає модель у слайсері, переносить витрату кожного пластику та час друку в інструмент і отримує мінімальний донат із розбивкою собівартості; повторювані вироби зберігає в каталог, де ціна щоразу перераховується з поточних налаштувань цін (PRD §1). Інструмент — одна система на комп'ютері автора; інтеграцій із зовнішніми сервісами немає. Межа довіри (trust boundary) — сам комп'ютер автора: інші пристрої в домашній мережі та сторонні сайти, відкриті в тому самому браузері, лежать **поза** нею, і інструмент їм не відповідає (AC-16, AC-16b).

**External systems (in / out):**

| Actor or system | Type | Interaction |
|---|---|---|
| автор | Person | Веде налаштування цін, рахує мінімальний донат, веде каталог — через браузер на `127.0.0.1` |
| Слайсер (Bambu Studio / OrcaSlicer) | System (external) | Джерело витрати пластику й часу друку; автор переносить значення **вручну** — інтеграції немає (імпорт файлу — етап 2, PRD §3) |
| Сторонній сайт у браузері автора | System (external, hostile) | Може спробувати надіслати запит до інструмента від імені автора (CSRF) або через DNS rebinding; запит відхиляється (AC-16b) |
| Інший пристрій у домашній мережі | System (external, hostile) | Може спробувати відкрити інструмент; сервер слухає лише `127.0.0.1`, тож з мережі він недосяжний (AC-16) |

**C4 Context (L1):**

```mermaid
C4Context
    title cost-calculator — System Context

    Person(author, "автор", "Мейкер з одним принтером; ставить мінімальний донат за виріб")
    System(calc, "calculate-3d", "Локальний інструмент: налаштування цін, розрахунок мінімального донату, каталог виробів")
    System_Ext(slicer, "Слайсер", "Bambu Studio / OrcaSlicer — показує витрату пластику й час друку")
    System_Ext(thirdparty, "Сторонній сайт", "Відкритий у тому самому браузері; поза межею довіри")
    System_Ext(landevice, "Інший пристрій у мережі", "Телефон чи інший комп'ютер у домашній мережі; поза межею довіри")

    Rel(author, slicer, "Нарізає модель, читає вагу й час")
    Rel(author, calc, "Вводить параметри, бачить мінімальний донат", "браузер, http://127.0.0.1")
    Rel(thirdparty, calc, "Спроба змінити чи прочитати дані (відхиляється)", "HTTP з браузера автора")
    Rel(landevice, calc, "Спроба відкрити інструмент (недосяжно)", "HTTP по LAN")
```

## 4. Solution strategy

**Target surface(s) (the first decision — what's being built):** `[backend-service, web-frontend]`

Автор працює з браузера, дані живуть у SQLite за FastAPI. Один процес на `127.0.0.1:8000` віддає і JSON API під `/api`, і зібраний React SPA (`make run`). Стек і цю пару поверхонь уже зафіксовано проєктним [ADR 0001](../../adr/0001-use-python-fastapi-and-react-vite-stack.md). Окремого ADR фічі немає: в її межах чесної альтернативи не існує. UI **перевикористовує** наявний фундамент (`architecture-map.md` §Frontend): shadcn/ui-примітиви з `web/src/shared/ui/` (Button, Input, Label, Card, Table + нові через `npx shadcn add`), токени з `web/src/app/styles/index.css`, лише Tailwind, TanStack Query + `openapi-fetch`. Прецедент екрана — `web/src/pages/home/`.

**Top strategic choices (the seeds for ADRs):**

1. **UI-architecture: SPA з URL-маршрутизацією (React Router, declarative mode)** — кожен екран має адресу (`/settings`, `/calculate`, `/catalog?q=…`, `/catalog/:itemId`), тож AC-09 («веде до налаштувань») і AC-14 («відкрити виріб») — це звичайні переходи, а F5 і «назад» працюють. Бекенд отримує SPA fallback: будь-який не-`/api` шлях віддає `index.html`. → [ADR 0001](adr/0001-route-spa-screens-with-react-router.md)
2. **Розрахунок лише на сервері** — формула собівартості існує в одному місці, у чистому доменному коді на точних `Fraction` з округленням через `Decimal` (ADR 0004, Amendment 2026-10-29), і її викликають і живий розрахунок, і каталог. UI після паузи в наборі запитує перерахунок і показує лише відповідь для поточних значень (AC-06). Точність (QG-1) переважує миттєвість (QG-2), і NFR сам міряє серверну відповідь. → [ADR 0002](adr/0002-compute-cost-on-server-only.md)
3. **Ціни каталогу — перерахунок при кожному читанні, пакетно** — без збереженої чи кешованої ціни. Фіксована кількість SQL-запитів (без N+1) + розрахунок у пам'яті; застаріла ціна неможлива за побудовою (AC-13, інваріант CONTEXT). → [ADR 0003](adr/0003-recompute-catalog-prices-on-every-read.md)
4. **Кількості — точні масштабовані цілі з одиницею в назві** — копійки `*_kop`, соті грама `*_cg`, десяті відсотка `*_permille`, секунди `*_s`. Спільний парсер вебу приймає кому чи крапку й відхиляє зайву точність; сервер валідує діапазони. Конвенцію `*_kop` поширено на всі дробові величини. → [ADR 0004](adr/0004-exchange-quantities-as-scaled-integers.md)

Each tactical decision in later sections should be traceable to one of these strategic seeds. Tactical decisions that *contradict* a strategic choice are red flags — surface them in §11 Risks.

## 5. Building block view

Модульний моноліт із простими шарами (проєктний ADR 0002): кожен доменний модуль — вертикальний зріз `router · schemas · service · repo · tables` за зразком `modules/health/`, і модулі звертаються один до одного лише через `service.py`. Фіча додає три модулі (→ [ADR 0005](adr/0005-split-feature-into-pricing-costing-catalog-modules.md)) із залежностями `catalog → costing → pricing`. Єдиний зворотний зв'язок — перевірка використання пластику для AC-03: його підставляє **роутер** `pricing` як параметр, тож сервіс `pricing` про каталог не знає. Веб — FSD-слайси, що збирають екрани з наявних shadcn/ui-примітивів.

**Internal decomposition (backend):**

```
backend/src/calculate3d/
├── main.py                 # + 3 routers, захист запитів (§8), SPA fallback (ADR 0001)
├── core/                   # config · db · errors · ids (+ спільні утиліти назв — §8)
└── modules/
    ├── pricing/            # налаштування цін
    │   ├── router.py       # /api/pricing — пластики CRUD, налаштування GET/PUT;
    │   │                   #   підставляє catalog.service.item_names_using_plastic у delete (AC-03)
    │   ├── schemas.py · service.py · repo.py
    │   └── tables.py       # пластики; налаштування цін — ОДИН рядок (нема рядка = «не задано», AC-09)
    ├── costing/            # розрахунок — нічого не зберігає
    │   ├── domain.py       # чиста формула на Fraction; донат ROUND_CEILING з точної суми,
    │   │                   #   рядки розбивки ROUND_HALF_UP (AC-08) — еталонна таблиця в tests/unit
    │   ├── service.py      # quote(): поточні ціни з pricing.service → domain
    │   └── router.py · schemas.py   # /api/costing
    └── catalog/            # вироби
        ├── router.py       # /api/catalog
        ├── schemas.py · service.py  # пакетне читання + costing.service для цін (ADR 0003)
        ├── repo.py
        └── tables.py       # вироби; витрата пластиків виробу (FK → пластик ON DELETE RESTRICT,
                            #   FK → виріб ON DELETE CASCADE)
```

**Internal decomposition (web, FSD):**

```
web/src/
├── app/            # BrowserRouter + Routes (ADR 0001), QueryProvider
├── pages/          # settings · calculate · catalog · item
├── widgets/        # cost-breakdown (мінімальний донат + 4 рядки; спільний для calculate та item)
├── features/       # edit-plastic · edit-price-settings · quote-form · save-item · delete-item
├── entities/       # plastic · price-settings · item · quote (TanStack Query хуки над @/shared/api)
└── shared/         # api (openapi-fetch) · ui (shadcn) · lib: parse-decimal (ADR 0004), format-money
```

Налаштування цін (тариф, потужність, знос, брак) зберігаються в **одній таблиці з одним рядком**: відсутній рядок = «не задано» (AC-09); збереження — заміна всіх полів в одній транзакції запиту (AC-04/05), тож очистити їх назад неможливо за побудовою. Точні колонки й одиниці (ADR 0004) визначає `generate-data-model`.

**C4 Container (L2):**

```mermaid
C4Container
    title cost-calculator — Containers

    Person(author, "автор", "Єдиний користувач, браузер на 127.0.0.1")

    System_Boundary(calc, "calculate-3d — один процес на 127.0.0.1:8000") {
        Container(spa, "Web SPA", "React 19, TypeScript, Vite, React Router, TanStack Query", "Екрани: налаштування цін, розрахунок, каталог, виріб; нічого не рахує")
        Container(api, "API", "Python 3.14, FastAPI", "JSON під /api, problem+json, захист запитів, віддає зібраний SPA")
        Container(pricing, "pricing", "модуль FastAPI", "Пластики й налаштування цін")
        Container(costing, "costing", "модуль FastAPI", "Формула собівартості на Fraction (округлення через Decimal); розрахунок не зберігає")
        Container(catalog, "catalog", "модуль FastAPI", "Вироби з витратою пластиків; ціни перераховує при читанні")
        ContainerDb(db, "SQLite", "файл backend/var/calculate3d.db, WAL", "Пластики, налаштування цін, вироби; без цін")
    }

    Rel(author, spa, "Вводить параметри, бачить мінімальний донат", "браузер")
    Rel(spa, api, "Розрахунок, налаштування, каталог", "JSON over HTTP /api")
    Rel(api, pricing, "Маршрутизує /api/pricing")
    Rel(api, costing, "Маршрутизує /api/costing")
    Rel(api, catalog, "Маршрутизує /api/catalog")
    Rel(catalog, costing, "Рахує ціну кожного виробу", "service.py")
    Rel(costing, pricing, "Бере поточні ціни", "service.py")
    Rel(pricing, catalog, "Хто використовує пластик (AC-03)", "параметр від router")
    Rel(pricing, db, "Читає і пише", "SQLAlchemy Core")
    Rel(catalog, db, "Читає і пише", "SQLAlchemy Core")
```

## 6. Runtime view

<!-- Seeded by architecture-design (3 flows). complete-sequence-diagrams (stage 06) fills §6 with -->
<!-- every critical flow / PRD §5 AC and closes with the US/AC → flow coverage table.              -->

### Додати або змінити пластик

(AC-01, AC-02; ADR 0004, ADR 0006)

```mermaid
sequenceDiagram
    autonumber
    actor U as user
    participant UI as ui
    participant S as service
    participant D as data-store

    Note over U,UI: Precondition: автор відкрив налаштування цін
    U->>UI: вводить назву і ціну за кілограм, зберігає
    UI->>UI: розбирає ціну з комою або крапкою у цілі копійки
    alt назва порожня або ціна не число, нуль, від'ємна чи із зайвою точністю
        UI-->>U: пояснення біля поля без мовчазного округлення, нічого не надіслано
    else поля коректні
        UI->>S: створити або змінити пластик з назвою і ціною
        S->>S: обрізає пробіли на краях, будує ключ назви без регістру, перевіряє межі ціни
        S->>D: шукає інший пластик з тим самим ключем назви
        D-->>S: збіг або нічого
        alt ціна поза межами на сервері
            S-->>UI: помилка валідації з назвою поля
            UI-->>U: пояснення біля поля ціни
        else назва вже є серед пластиків
            S-->>UI: помилка домену назва зайнята, поле назви
            UI-->>U: назва обов'язкова і має бути унікальною
        else назва вільна
            S->>D: записує пластик з назвою, ключем назви і ціною
            Note over S,D: persists plastic (unique lookup by name key)
            D-->>S: записано
            S-->>UI: пластик з ідентифікатором
            UI-->>U: пластик у списку і доступний для вибору в розрахунку
        end
    end
    Note over U,UI: Postcondition: назви пластиків унікальні без урахування регістру й пробілів на краях
```

### Critical flow 3: видалення пластику, який використовують вироби

(AC-03, failure mode; ADR 0005)

```mermaid
sequenceDiagram
    actor author as автор
    participant spa as Web SPA
    participant api as API
    participant pricing as pricing
    participant catalog as catalog
    participant db as SQLite
    author->>spa: видаляє пластик PLA білий
    spa->>api: видалити пластик
    api->>pricing: delete_plastic з функцією used_by від роутера
    pricing->>catalog: які вироби використовують цей пластик
    catalog->>db: назви виробів із цим пластиком
    db-->>catalog: Підставка, Органайзер
    catalog-->>pricing: список назв
    alt список не порожній
        pricing-->>api: помилка домену пластик використовується, з назвами
        api-->>spa: problem+json з кодом і назвами виробів
        spa-->>author: видалити не можна, назви виробів, ціну змінити можна
    else ніхто не використовує
        pricing->>db: видаляє пластик
        Note over pricing,db: FK RESTRICT відхилить видалення, якщо перевірку колись оминуть
        db-->>pricing: видалено
        pricing-->>api: готово
        api-->>spa: успіх без тіла
        spa-->>author: пластик зник зі списку
    end
```

### Зберегти налаштування цін

(AC-04, AC-05; ADR 0002, ADR 0004)

```mermaid
sequenceDiagram
    autonumber
    actor U as user
    participant UI as ui
    participant S as service
    participant D as data-store

    Note over U,UI: Precondition: автор відкрив налаштування цін, налаштувань може ще не бути
    U->>UI: заповнює тариф, потужність, ціну принтера, термін служби, деталі і брак, зберігає
    UI->>UI: розбирає кожне поле у масштабоване ціле
    alt хоч одне поле порожнє, не число чи із зайвою точністю
        UI-->>U: пояснення для кожного хибного поля з межами і точністю, нічого не надіслано
    else усі поля розібрано
        UI->>S: замінити всі налаштування цін однією дією
        S->>S: перевіряє межі кожного поля, термін служби більший за нуль, брак від 0 до 100 відсотків
        alt хоч одне поле поза межами
            S-->>UI: помилка валідації з переліком полів
            UI-->>U: пояснення біля кожного поля, жодну зміну не збережено
        else усі поля в межах
            S->>D: вставляє або замінює єдиний рядок налаштувань усіма полями разом
            Note over S,D: persists price settings (single row, full replace in one transaction)
            D-->>S: записано
            S->>S: знос за годину з точного значення, для показу округлено до копійки
            S-->>UI: збережені налаштування і знос за годину
            UI-->>U: знос 7,00 ₴ за годину друку
        end
    end
    Note over U,UI: Postcondition: усі поля збережено разом, очистити їх до «не задано» неможливо
```

### Critical flow 1: живий перерахунок мінімального донату

(AC-06, AC-07, AC-09; ADR 0002, ADR 0004)

```mermaid
sequenceDiagram
    actor author as автор
    participant spa as Web SPA
    participant api as API
    participant costing as costing
    participant pricing as pricing
    participant db as SQLite
    author->>spa: змінює витрату пластику або час друку
    spa->>spa: розбирає текст у масштабовані цілі
    alt поле хибне (порожнє, нуль, зайва точність, понад межу, повтор пластику)
        spa-->>author: пояснення біля поля, донат не показано, зберегти не можна
    else усі поля коректні
        spa->>spa: чекає паузу в наборі, ключ запиту = введені значення
        spa->>api: розрахувати собівартість для введених значень
        api->>costing: quote з витратою пластиків і часом
        costing->>pricing: поточні ціни пластиків і налаштування цін
        pricing->>db: читає пластики та рядок налаштувань
        db-->>pricing: дані або налаштувань немає
        alt налаштувань цін бракує
            pricing-->>costing: налаштування не задано
            costing-->>api: помилка домену з переліком відсутнього
            api-->>spa: problem+json з кодом і переліком
            spa-->>author: що саме бракує і посилання на налаштування цін
        else налаштування є
            pricing-->>costing: ціни
            costing->>costing: точна сума у Fraction, донат округлено вгору, рядки до копійки
            costing-->>api: мінімальний донат і 4 рядки розбивки
            api-->>spa: результат у копійках
            spa-->>author: донат і розбивка, лише якщо ключ досі збігається з полями
        end
    end
```

### Зберегти виріб у каталог (створення або редагування)

(AC-10, AC-11, AC-14b, AC-14c; ADR 0003, ADR 0006)

```mermaid
sequenceDiagram
    autonumber
    actor U as user
    participant UI as ui
    participant S as service
    participant D as data-store

    Note over U,UI: Precondition: розрахунок або відкритий виріб показує мінімальний донат для поточних полів
    U->>UI: вводить назву виробу і зберігає
    alt донат не показано через помилки введення або брак налаштувань
        UI-->>U: зберегти не можна, дія недоступна
    else донат показано
        UI->>S: зберегти новий виріб або зміну наявного з назвою, витратою пластиків і часом друку
        S->>S: обрізає пробіли на краях, будує ключ назви, перевіряє витрату, час і повтор пластику
        S->>D: шукає інший виріб з тим самим ключем назви і перевіряє, що пластики існують
        D-->>S: збіг або нічого
        alt назва порожня або вже є в каталозі
            S-->>UI: помилка домену назва обов'язкова або зайнята
            UI-->>U: назва обов'язкова і унікальна в каталозі
        else параметри порушують правила розрахунку або пластику не існує
            S-->>UI: помилка валідації з назвою поля
            UI-->>U: пояснення біля поля, виріб у каталозі лишається з попередніми параметрами
        else усе коректно
            S->>D: записує виріб і замінює всі його рядки витрати пластиків
            Note over S,D: persists item + item plastic usage (atomic, one transaction, no price)
            D-->>S: записано
            S-->>UI: виріб з ідентифікатором, без ціни
            UI-->>U: виріб у каталозі з поточними параметрами
        end
    end
    Note over U,UI: Postcondition: каталог зберігає лише параметри, прибраний з виробу пластик знову можна видалити
```

### Critical flow 2: відкриття каталогу з перерахунком цін

(AC-12, AC-13; ADR 0003)

```mermaid
sequenceDiagram
    actor author as автор
    participant spa as Web SPA
    participant api as API
    participant catalog as catalog
    participant costing as costing
    participant pricing as pricing
    participant db as SQLite
    author->>spa: відкриває каталог, вводить частину назви
    spa->>api: список виробів з фільтром за назвою
    api->>catalog: list з рядком пошуку
    catalog->>db: усі вироби та їхня витрата пластиків одним пакетом
    db-->>catalog: вироби з рядками витрати
    catalog->>catalog: фільтр без урахування регістру, абетковий порядок
    catalog->>costing: порахувати мінімальний донат для пакета виробів
    costing->>pricing: поточні ціни, один раз на весь пакет
    pricing->>db: читає пластики та рядок налаштувань
    db-->>pricing: ціни
    pricing-->>costing: ціни
    costing-->>catalog: мінімальний донат кожного виробу
    catalog-->>api: відсортований список з донатами
    api-->>spa: список у копійках
    spa-->>author: вироби з актуальними цінами
```

### Відкрити виріб

(AC-14; ADR 0002, ADR 0003)

```mermaid
sequenceDiagram
    autonumber
    actor U as user
    participant UI as ui
    participant S as service
    participant D as data-store

    Note over U,UI: Precondition: виріб є в каталозі
    U->>UI: відкриває виріб з каталогу
    UI->>S: отримати виріб з розрахунком
    S->>D: читає виріб і його рядки витрати пластиків за ідентифікатором
    D-->>S: виріб або нічого
    alt виробу немає
        S-->>UI: помилка домену виріб не знайдено
        UI-->>U: виріб не знайдено, перехід до каталогу
    else виріб є
        S->>D: читає поточні ціни пластиків і рядок налаштувань
        D-->>S: ціни
        S->>S: та сама формула, що й у розрахунку, донат вгору, рядки до копійки
        S-->>UI: параметри, мінімальний донат і 4 рядки розбивки
        UI-->>U: параметри, донат і розбивка так само, як у розрахунку
    end
    Note over U,UI: Postcondition: нічого не записано, ціна відповідає поточним налаштуванням
```

### Видалити виріб

(AC-15)

```mermaid
sequenceDiagram
    autonumber
    actor U as user
    participant UI as ui
    participant S as service
    participant D as data-store

    Note over U,UI: Precondition: виріб є в каталозі
    U->>UI: видаляє виріб
    UI-->>U: просить підтвердити видалення
    alt автор скасовує
        UI-->>U: виріб лишається без змін, запит не надіслано
    else автор підтверджує
        UI->>S: видалити виріб
        S->>D: видаляє виріб, його рядки витрати пластиків зникають каскадно
        Note over S,D: hard delete item, cascade item plastic usage
        D-->>S: видалено
        S-->>UI: готово
        UI-->>U: виріб зник з каталогу
    end
    Note over U,UI: Postcondition: пластики, які використовував лише цей виріб, знову можна видалити
```

### Cross-cutting: захист локального API

(AC-16, AC-16b; ADR 0007, ADR 0004 проєкту)

```mermaid
sequenceDiagram
    autonumber
    actor U as user
    participant UI as ui
    participant C as client
    participant S as service
    participant D as data-store

    Note over C,S: Precondition: сервіс слухає лише локальну адресу комп'ютера автора, client = інший пристрій або сторонній сайт
    alt інший пристрій у мережі
        C->>S: намагається з'єднатися через мережеву адресу
        Note over C,S: з'єднання неможливе, сервіс не слухає зовнішніх адрес
    else чужа адреса хоста, зокрема DNS rebinding
        C->>S: будь-який запит
        S->>S: звіряє адресу хоста зі списком дозволених
        S-->>C: відмова, хост не дозволено
    else сторонній сайт у браузері автора
        C->>S: запит до API від імені автора
        S->>S: перевіряє ознаку міжсайтового запиту і джерело
        S-->>C: відмова, запит з чужого джерела, дані не віддано
    else змінний запит не у форматі JSON
        C->>S: зміна через просту форму
        S-->>C: відмова, непідтримуваний формат
    else запит з інтерфейсу автора
        U->>UI: будь-яка дія
        UI->>S: запит з того самого джерела
        S->>S: хост дозволений, джерело те саме
        S->>D: виконує дію запиту
        D-->>S: результат
        S-->>UI: відповідь
        UI-->>U: результат дії
    end
    Note over C,S: Postcondition: чужі джерела не змінюють і не читають налаштувань цін і каталогу
```

### Coverage: US/AC → flows

| ID | Realized by (§6 heading) | How | Note |
|---|---|---|---|
| US-01 | `Додати або змінити пластик`, `Critical flow 3: видалення пластику, який використовують вироби` | flow | |
| US-02 | `Зберегти налаштування цін` | flow | |
| US-03 | `Critical flow 1: живий перерахунок мінімального донату` | flow | |
| US-04 | `Зберегти виріб у каталог (створення або редагування)` | flow | |
| US-05 | `Critical flow 2: відкриття каталогу з перерахунком цін` | flow | |
| US-06 | `Відкрити виріб`, `Зберегти виріб у каталог (створення або редагування)`, `Видалити виріб` | flow | |
| AC-01 | `Додати або змінити пластик` | flow | |
| AC-02 | `Додати або змінити пластик` | branch | `alt назва порожня або ціна не число, нуль, від'ємна чи із зайвою точністю` · `else ціна поза межами на сервері` · `else назва вже є серед пластиків` |
| AC-03 | `Critical flow 3: видалення пластику, який використовують вироби` | branch | `alt список не порожній` |
| AC-04 | `Зберегти налаштування цін` | flow | |
| AC-05 | `Зберегти налаштування цін` | branch | `alt хоч одне поле порожнє, не число чи із зайвою точністю` · `alt хоч одне поле поза межами` |
| AC-06 | `Critical flow 1: живий перерахунок мінімального донату` | flow | |
| AC-06b | `Critical flow 1: живий перерахунок мінімального донату` | flow | сума за кожним пластиком у кроці costing |
| AC-07 | `Critical flow 1: живий перерахунок мінімального донату` | branch | `alt поле хибне (порожнє, нуль, зайва точність, понад межу, повтор пластику)` — межі 1 000 000 г, 100 000 год, 32 пластики |
| AC-08 | `Critical flow 1: живий перерахунок мінімального донату` | flow | крок «точна сума у Fraction, донат округлено вгору, рядки до копійки» |
| AC-08b | `Critical flow 1: живий перерахунок мінімального донату` | flow | той самий крок округлення |
| AC-09 | `Critical flow 1: живий перерахунок мінімального донату` | branch | `alt налаштувань цін бракує` |
| AC-10 | `Зберегти виріб у каталог (створення або редагування)` | flow | + `alt донат не показано через помилки введення або брак налаштувань` |
| AC-11 | `Зберегти виріб у каталог (створення або редагування)` | branch | `alt назва порожня або вже є в каталозі` |
| AC-12 | `Critical flow 2: відкриття каталогу з перерахунком цін` | flow | |
| AC-13 | `Critical flow 2: відкриття каталогу з перерахунком цін` | flow | ціни читаються при кожному відкритті |
| AC-14 | `Відкрити виріб` | flow | |
| AC-14b | `Зберегти виріб у каталог (створення або редагування)` | flow | зміна наявного виробу |
| AC-14c | `Зберегти виріб у каталог (створення або редагування)` | branch | `else параметри порушують правила розрахунку або пластику не існує` · `alt назва порожня або вже є в каталозі` |
| AC-15 | `Видалити виріб` | flow | + `alt автор скасовує` |
| AC-16 | `Cross-cutting: захист локального API` | branch | `alt інший пристрій у мережі` · `else чужа адреса хоста, зокрема DNS rebinding` |
| AC-16b | `Cross-cutting: захист локального API` | branch | `else сторонній сайт у браузері автора` · `else змінний запит не у форматі JSON` |

Coverage: 6/6 user stories · 21/21 ACs — 0 non-runtime N/A.

**Flags:**
- Seeded-потоки `Critical flow 1–3` (від architecture-design) мають конкретних учасників (`Web SPA`, `API`, `pricing`/`costing`/`catalog`, `SQLite`) замість генеричних. Їх не переписано (адитивне правило): лише заголовки піднято до `###` і блоки впорядковано за §4. Генерична перемальовка — свідома ручна правка.
- `client` (інший пристрій у мережі або сторонній сайт у браузері автора) у `Cross-cutting: захист локального API` — зовнішній ініціатор загрози, не контейнер §5. Позначено для architecture-design (§3 Context може згадати його як зовнішнього актора).
- Підказки для generate-data-model з persist/read-кроків: унікальний ключ назви пластику і виробу (ADR 0006); пошук виробів за пластиком (`Critical flow 3`) ⇒ індекс на пластик у рядках витрати; рядки витрати читаються за виробом (`Відкрити виріб`, `Critical flow 2` пакетом); налаштування цін — один рядок, повна заміна.
- Нових ADR-кандидатів немає.

## 7. Deployment view

Топологія не змінюється (ADR 0004): **один процес Uvicorn на `127.0.0.1:8000`** (`make run` = migrate → build `web/dist` → serve) віддає і зібраний SPA, і `/api`. БД — один файл `backend/var/calculate3d.db` (WAL) поруч. У розробці (`make dev`) працюють два процеси: Uvicorn `--reload` на :8000 і Vite на :5173, який проксіює `/api` на :8000. Реплік, контейнерів, фонових воркерів і деплою немає.

**Що змінює фіча:**
- **SPA fallback** — будь-який не-`/api` шлях віддає `web/dist/index.html`, щоб прямі посилання `/catalog/<id>` працювали після F5 (ADR 0001). Невідомі `/api/*` і далі повертають problem+json 404.
- **Перелік дозволених адрес** для захисту запитів (§8, ADR 0007) має містити обидва локальні порти: `127.0.0.1`/`localhost` на :8000 (`make run`) і :5173 (Vite у `make dev`, бо проксі зберігає `Host` і `Origin` браузера).
- Міграції нових таблиць накочуються наявним `make migrate` (його викликає `make run`).

**Monitoring:**
- Метрик, алертів і трасування немає свідомо: локальний інструмент для одного користувача.
- Консольний access log Uvicorn + наявний `GET /api/health` (стан БД).
- NFR (latency, точність, збереженість) перевіряються автоматичними тестами в `make check`, а не моніторингом у рантаймі (§10).

**Scaling thresholds:**
- Розраховано на обсяг з PRD §6: **1 000 виробів і 50 пластиків**; реальне використання — ≈3 розрахунки на тиждень і каталог із десятків виробів.
- **Тригер перегляду ADR 0003** (перерахунок каталогу при кожному читанні): тест каталогу на обсязі з PRD §6 перевищує p95 ≤ 500 мс → спершу пагінація відповіді каталогу, потім (якщо не допоможе) кеш цін за тим самим інтерфейсом сервісу.
- Резервна копія — ручне копіювання файлу БД (разом із `-wal`) або `sqlite3 … ".backup"`; автоматичного бекапу немає (прийнятий борг, §11).

## 8. Crosscutting concepts

| Concept | Convention | Where defined |
|---|---|---|
| Logging / observability | Консольний access log Uvicorn + `GET /api/health`; метрик і трасування немає (локальний інструмент, §7) | repo default |
| Authentication | Немає — інструмент доступний лише з комп'ютера автора | ADR 0004 (проєкт) |
| **Request guard (AC-16, AC-16b)** | Bind `127.0.0.1` + middleware у `core`: allowlist `Host` (`127.0.0.1`/`localhost` × порти :8000 і :5173) → `400 host_not_allowed`; для `/api` відмова при `Sec-Fetch-Site` cross-site/same-site чи чужому `Origin` → `403 cross_origin_forbidden`; змінні запити — лише `application/json` (`415`); `CORSMiddleware` не додається | [ADR 0007](adr/0007-guard-local-api-with-host-allowlist-and-same-origin-checks.md) |
| Error handling | `AppError(code, message, status)` → RFC 9457 problem+json. Коди з простором імен модуля (`pricing.plastic_in_use`, `pricing.name_taken`, `costing.settings_missing`, `catalog.name_taken`, …). **Доповнення:** `AppError` отримує необов'язкові поля-розширення (`field` — яке поле підсвітити; `items` — назви виробів для AC-03; `missing` — яких налаштувань бракує для AC-09), які `problem()` додає в тіло. 422 уже має `errors[{loc, msg}]` | `core/errors.py` + тут |
| ID strategy | UUIDv7 у застосунку (`core/ids.py::new_id()`), `TEXT` 36 символів | `CLAUDE.md` |
| Money & units | Масштабовані цілі з одиницею в назві (`*_kop`, `*_cg`, `*_permille`, `*_s`, `*_w`); точні `Fraction` лише всередині формули, округлення через `Decimal`; мінімальний донат — `ROUND_CEILING` з точної суми; рядки розбивки й показ зносу за годину — `ROUND_HALF_UP` до копійки (AC-04, AC-08) | [ADR 0002](adr/0002-compute-cost-on-server-only.md), [ADR 0004](adr/0004-exchange-quantities-as-scaled-integers.md) |
| **Names (пластик, виріб)** | `name` без пробілів на краях + `name_key = casefold(name)` з UNIQUE-індексом; пошук (підрядок у casefold) і сортування (латиниця, потім українська абетка) — у Python через `core/text.py`; SQL `LIKE`/`NOCASE` для назв не використовуються (ASCII-only) | [ADR 0006](adr/0006-enforce-name-uniqueness-via-casefolded-name-key.md) |
| Input parsing (web) | Спільний парсер `shared/lib/parse-decimal`: кома або крапка, зайва точність → помилка біля поля без округлення; повертає ціле в потрібній одиниці | [ADR 0004](adr/0004-exchange-quantities-as-scaled-integers.md) |
| Internationalisation | Увесь текст UI українською; людський текст помилки UI формує за `code` (+ `field`/`items`/`missing`), а серверний `detail` — лише запасний технічний текст; гроші — `Intl.NumberFormat('uk-UA', {style:'currency', currency:'UAH'})` з копійок | `web/CLAUDE.md` + тут |
| XSS | Назви завжди рендеряться як текст (React екранує за замовчуванням); `dangerouslySetInnerHTML` для даних користувача заборонено (PRD §6.1) | тут |
| Transactions | Одна транзакція на запит (`ConnectionDep`, commit до відповіді). Виріб разом із рядками витрати пластиків і вся форма налаштувань цін пишуться атомарно — або все, або нічого (AC-05, AC-14c) | `core/db.py` |
| Concurrency | Один користувач: перемагає останній запис, без оптимістичних блокувань і версій рядків. На UI стару відповідь розрахунку відкидає ключ запиту (ADR 0002) | тут |
| Durability | SQLite WAL + commit до відправки відповіді; налаштування `synchronous` — дефолт драйвера | `core/db.py` |
| Delete confirmation | Підтвердження видалення виробу й пластику — лише в UI (AC-15); API видаляє одразу | тут |
| Outbox / events | N/A — синхронні виклики `service.py` в одному процесі (ADR 0002 проєкту) | — |

## 9. Architecture decisions

| # | Title | Status | Section |
|---|---|---|---|
| [0001](adr/0001-route-spa-screens-with-react-router.md) | Route SPA screens with React Router and serve index.html for every non-API path | Accepted | §4 |
| [0002](adr/0002-compute-cost-on-server-only.md) | Compute cost on the server only; the UI re-requests a quote on every field change | Accepted | §4 |
| [0003](adr/0003-recompute-catalog-prices-on-every-read.md) | Recompute catalog prices on every read in one batched pass, never cache them | Accepted | §4 |
| [0004](adr/0004-exchange-quantities-as-scaled-integers.md) | Exchange every fractional quantity as an exact scaled integer named after its unit | Accepted | §4 |
| [0005](adr/0005-split-feature-into-pricing-costing-catalog-modules.md) | Split the feature into pricing, costing and catalog modules; pricing gets item usage by parameter | Accepted | §5 |
| [0006](adr/0006-enforce-name-uniqueness-via-casefolded-name-key.md) | Enforce name uniqueness via a casefolded name_key column; search and sort names in Python | Accepted | §8 |
| [0007](adr/0007-guard-local-api-with-host-allowlist-and-same-origin-checks.md) | Guard the local API with a Host allowlist and same-origin checks instead of CSRF tokens | Accepted | §8 |

ADR files live under `docs/features/cost-calculator/adr/NNNN-<title>.md`.

**Project-level ADRs this feature builds on** (not re-decided here): [0001](../../adr/0001-use-python-fastapi-and-react-vite-stack.md) stack + surfaces · [0002](../../adr/0002-organize-as-modular-monolith-with-simple-layers.md) modular monolith · [0003](../../adr/0003-store-data-in-sqlite-via-sqlalchemy-core-and-alembic.md) SQLite, IDs, money · [0004](../../adr/0004-run-local-only-without-authentication.md) local-only, no auth.

## 10. Quality requirements

Кожна ціль із §1 розгорнута в сценарій. Числа — дослівно з PRD §6.

**QG-1. Точність розрахунку**
- **When:** формула рахує розрахунок для кожного рядка еталонної таблиці ≥ 10 контрольних прикладів (зокрема AC-06, AC-06b, AC-08b, AC-13), а каталог перераховує ті самі вироби.
- **Then:** 100 % збіг до копійки з еталонною таблицею ≥ 10 контрольних прикладів (зокрема AC-06, AC-06b, AC-08b, AC-13); 0 випадків, коли мінімальний донат менший за собівартість.
- **How verify:** автоматичні тести проти еталонної таблиці. (1) Параметризований pytest над чистою формулою `costing.domain` (`tests/unit/`) з очікуваними мінімальним донатом і чотирма рядками розбивки в копійках. (2) Перевірка на детерміновано згенерованих вхідних даних (фіксований seed), що мінімальний донат × 1 коп ≥ точна сума (`Fraction`) і менший за неї + 1 коп. (3) Інтеграційний тест: для тих самих параметрів ендпоінт розрахунку і каталог повертають однаковий мінімальний донат (ADR 0002, ADR 0003).

**QG-2. Чуйність**
- **When:** (a) запит розрахунку після зміни поля; (b) запит каталогу з перерахунком цін усіх виробів на згенерованих даних (1 000 виробів, 50 пластиків).
- **Then:** (a) Latency p95 перерахунку мінімального донату після зміни поля розрахунку ≤ 300 мс; (b) Latency p95 відкриття каталогу ≤ 500 мс — час відповіді сервера на локальній машині (відмальовування в браузері не входить).
- **How verify:** інтеграційні тести в `tests/integration/` через `TestClient` на справжньому тимчасовому SQLite-файлі: прогрів, далі ≥ 50 вимірів `time.perf_counter()`, p95 через `statistics.quantiles(…, n=20)[18]`, порівняння з порогом. Запускаються в `make check` на локальній машині автора; **пропускаються, коли задано змінну середовища `CI`** (GitHub Actions), бо PRD міряє «на локальній машині», а спільні ранери дають хибно-червоні прогони.

**QG-3. Доступ лише автору**
- **When:** (a) хтось відкриває інструмент з іншого пристрою в домашній мережі; (b) запит із чужим `Host` (DNS rebinding); (c) запит з `Origin` стороннього сайту або `Sec-Fetch-Site: cross-site`; (d) змінний запит не з `application/json` (HTML-форма стороннього сайту).
- **Then:** інструмент для нього недоступний: налаштування цін і каталог бачить і змінює лише автор на своєму комп'ютері (AC-16); інструмент не приймає змін і не віддає даних стороннім сайтам (AC-16b): (a) з'єднання не встановлюється; (b) `400 host_not_allowed`; (c) `403 cross_origin_forbidden`; (d) `415`; після кожної відмови дані не змінено.
- **How verify:** (a) наявний `tests/unit/test_run.py` (bind = `127.0.0.1` навіть при `CALC3D_HOST=0.0.0.0`) + ручна спроба з телефону під час легкого security review; (b)–(d) інтеграційні тести middleware (ADR 0007) з перевіркою, що після відмови стан БД незмінний; щасливий шлях з дозволеним `Host`/`Origin` теж покрито.

**QG-4. Збереженість**
- **When:** автор зберіг налаштування цін, пластик і виріб, після чого інструмент чи комп'ютер перезапущено.
- **Then:** 100 % збережених змін доступні після перезапуску інструмента чи комп'ютера.
- **How verify:** інтеграційний тест «зберегти → перезапустити → прочитати»: запис через `TestClient` першого `create_app()`, `engine.dispose()`, новий `create_app()` на тому самому файлі БД, читання й порівняння всіх полів.

**Додатково (PRD §6, поза топ-цілями) — Локалізація**
- **Then:** 100 % текстів інтерфейсу українською; гроші у форматі «115,25 ₴».
- **How verify:** тест інтерфейсу (vitest на `shared/lib/format-money`: 11525 коп → «115,25 ₴» з нерозривним пробілом, який ставить `Intl`) + ручний перегляд перед релізом.

## 11. Risks and technical debt

| Risk / debt | Severity | Mitigation | Owner |
|---|---|---|---|
| Правила округлення застосовано не там: `ROUND_CEILING` до рядків розбивки чи `ROUND_HALF_UP` до мінімального донату, або донат рахується з округлених рядків (AC-08) | Medium | Одна чиста функція в `costing.domain` (ADR 0002); еталонна таблиця QG-1 перевіряє і донат, і чотири рядки, зокрема AC-08b, де сума рядків відрізняється від донату | автор |
| На екрані лишається ціна для попередніх значень через debounce або відповіді, що прийшли не в тому порядку (AC-06) | Medium | Ключ запиту TanStack Query = нормалізовані введені значення; показується лише відповідь для поточного ключа; vitest на сценарій «дві швидкі зміни, повільна перша відповідь» | автор |
| UI-парсер — єдиний захист від зайвої точності (ADR 0004): баг у ньому мовчки округлить 649,995 ₴ | Medium | Unit-тести `shared/lib/parse-decimal` на всі приклади з AC-01/02/05/07 (кома, крапка, зайві знаки, нуль, від'ємне, не число) | автор |
| Тести latency QG-2 залежать від машини; на CI вони пропускаються, тож регресію швидкодії видно лише в локальному `make check` | Low | Правило `CLAUDE.md`: `make check` перед кожним комітом; тест каталогу на обсязі з NFR — тригер перегляду ADR 0003 (§7) | автор |
| `docs/architecture-map.md` описує стан до scaffold (`reflects_commit: 95f8e06`), тож наступні стадії можуть спертися на застарілі анкори | Low | Запустити `/sdlc:map-architecture` після цього проходу; до того часу джерело конвенцій — `CLAUDE.md` | автор |
| Перелік дозволених адрес (ADR 0007) розсинхронізується з портами `make run`/`make dev` → `400` на кожен запит у розробці або надто широкий перелік | Low | Перелік виводиться з тих самих налаштувань портів; інтеграційний тест на обидва порти | автор |
| PRD §8: брак, залежний від тривалості друку, або окремий тариф для генератора змінять форму налаштувань цін (зараз один рядок) і формулу | Low | Налаштування доступні лише через `pricing.service`, а формула — лише в `costing.domain` (ADR 0005), тож зміна локалізована: міграція + одна функція. Переглянути після 30 днів використання етапу 1 (термін PRD §8) | автор |
| PRD §8: поля файлу слайсера для імпорту (етап 2) невідомі | Low | Імпорт — окремий майбутній модуль, що лише заповнює вхід розрахунку (ADR 0005); ручне введення лишається запасним шляхом. Вирішити перед `/sdlc:write-prd` фічі імпорту (термін PRD §8) | автор |
| Каталог переросте обсяг з NFR (1 000 виробів), і перерахунок при кожному читанні стане повільним | Low | Тригер у §7: пагінація, потім кеш за інтерфейсом сервісу (ADR 0003) | автор |
| Браузер без `Sec-Fetch-Site` (дуже старий) — захист від CSRF тримається лише на `Origin` + JSON-only | Low | Автор користується сучасним браузером; `Host` allowlist однаково зупиняє DNS rebinding (ADR 0007) | автор |

**Accepted debt (acceptable in v1, plan to fix later):**
- Немає автоматичного бекапу БД — лише ручне копіювання файлу (§7).
- Каталог без пагінації: кожне читання перераховує всі вироби (ADR 0003).
- Перевірку «надто точне значення» виконує лише UI-парсер; сервер бачить уже ціле число (ADR 0004).
- Конвенцію одиниць у `CLAUDE.md` треба оновити під час імплементації: маса з дробовою точністю — `*_cg` (замість `*_g`), частки відсотка — `*_permille` (ADR 0004, §1 Decision overrides).
- Немає історії цін і розрахунків — свідомий non-goal (PRD §3), а не борг, що чекає виправлення.

## 12. Glossary

Доменні терміни — канонічно в кореневому [CONTEXT.md](../../../CONTEXT.md) (він перемагає за розбіжності); тут — ті, що вжито в цьому SAD, плюс технічні терміни архітектури.

| Term | Meaning |
|---|---|
| автор | Єдиний користувач інструмента: мейкер, який друкує вироби на власному принтері й віддає їх за донат на ЗСУ (CONTEXT). |
| брак | Відсоткова надбавка до собівартості, що в середньому покриває невдалі друки (CONTEXT). |
| виріб | Модель у каталозі зі збереженими параметрами друку (витрата пластиків, час друку); готової ціни не зберігає (CONTEXT). |
| витрата пластику | Маса одного пластику в грамах (до 0,01 г) на один друк разом із промивкою й підтримками (CONTEXT). |
| знос | Амортизація принтера плюс деталі, що зношуються, у перерахунку на годину друку (CONTEXT). |
| каталог | Усі збережені вироби з унікальними назвами, кожен із мінімальним донатом, перерахованим у момент перегляду (CONTEXT). |
| мінімальний донат | Собівартість, округлена вгору до цілої копійки (CONTEXT). |
| налаштування цін | Єдиний поточний набір вхідних цін: пластики з цінами, тариф, потужність, дані для зносу, брак (CONTEXT). |
| пластик | Вид філаменту в налаштуваннях цін із поточною ціною за кілограм (CONTEXT). |
| розбивка собівартості | Чотири рядки (пластик, електрика, знос, брак), кожен округлений до копійки за звичайними правилами (CONTEXT). |
| розрахунок | Введені зараз витрати й час разом із мінімальним донатом і розбивкою; існує лише на екрані, доки його не збережено як виріб (CONTEXT). |
| собівартість | Пластик + електрика + знос + брак для одного виробу з поточних налаштувань цін (CONTEXT). |
| масштабоване ціле | Дробова величина, записана цілим числом у найменшій допустимій одиниці з одиницею в назві поля (`*_kop`, `*_cg`, `*_permille`, `*_s`) — ADR 0004. |
| `name_key` | Службова колонка з назвою після trim + `casefold()`; на ній UNIQUE-індекс для унікальності без урахування регістру — ADR 0006. |
| межа довіри (trust boundary) | Комп'ютер автора; запити з-поза нього (інші пристрої, сторонні сайти в браузері) не приймаються — §3, ADR 0007. |
| DNS rebinding | Атака, коли чужий домен переключає свій DNS на `127.0.0.1`, щоб браузер вважав запити до інструмента своїми; зупиняється перевіркою `Host` — ADR 0007. |
| CSRF | Cross-site request forgery: стороння сторінка шле запит до інструмента з браузера автора; зупиняється перевіркою `Origin`/`Sec-Fetch-Site` + JSON-only — ADR 0007. |
| SPA fallback | Віддача `index.html` на будь-який не-`/api` шлях, щоб прямі посилання на екрани SPA працювали — ADR 0001. |
| quote | Технічна назва операції розрахунку в модулі `costing` (`service.quote()`); не зберігається — ADR 0002, ADR 0005. |
