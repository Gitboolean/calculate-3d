---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-28"
feature_size: M
stage: "04-05"
ticket: ""
---

# 0001 — Route SPA screens with React Router and serve index.html for every non-API path

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Anton Pohorielov (автор), architecture-design pass

## Context

Проєктний ADR 0001 уже зафіксував React SPA, яку FastAPI віддає разом з API. Фіча cost-calculator додає чотири екрани: налаштування цін, розрахунок, каталог і виріб. AC-09 вимагає «вести до налаштувань», коли їх бракує, а AC-14 — «відкрити виріб» з каталогу. Скаффолд маршрутизації не має (`web/src/app/App.tsx` рендерить одну `HomePage`), а `StaticFiles(html=True)` у `main.py` віддає 404 на будь-який глибокий шлях на кшталт `/catalog/<id>`.

## Decision drivers

- AC-09 (перехід до налаштувань), AC-12 (пошук у каталозі), AC-14 (відкрити виріб) — потрібні адресовані екрани.
- §2: FSD-шари `app → pages` під контролем Steiger; бюджет одна людина × 2–4 тижні — мінімум нових понять.
- §2: один процес на `127.0.0.1:8000` віддає і SPA, і `/api` (ADR 0001, ADR 0004).

## Considered options

1. **SPA + React Router v7 у declarative mode** — `<BrowserRouter>` + `<Routes>`; кожен екран має URL; бекенд віддає `index.html` на будь-який не-`/api` шлях.
2. **SPA + TanStack Router** — типізовані параметри й search params, інтеграція з TanStack Query через loaders; файловий режим додає кодогенерацію поруч із FSD.
3. **SPA без роутера (вкладки в стані React)** — нуль залежностей, але F5 скидає екран, немає «назад» і посилань на виріб.

## Decision outcome

**Chosen:** Option 1. Це найменший приріст понять, за який отримуємо адресовані екрани: `/settings`, `/calculate`, `/catalog` (пошук у `?q=`), `/catalog/:itemId`. Маршрути оголошуються в шарі `app` (`web/src/app/`), екрани — це слайси `pages/`. Бекенд отримує SPA fallback: усі шляхи, що не починаються з `/api`, віддають `web/dist/index.html`, а невідомі `/api/*` і далі повертають problem+json 404.

## Consequences

**Positive**
- Перезавантаження сторінки, «назад» і закладки працюють; AC-09 зводиться до звичайного посилання на `/settings`.
- Пошуковий рядок каталогу живе в URL (`?q=`), тож переживає F5.
- Declarative mode не нав'язує власних data loaders: дані й далі тягне TanStack Query, як у scaffold-прецеденті `entities/health`.

**Negative**
- Нова runtime-залежність `react-router`.
- Бекенд мусить мати catch-all для SPA, і він не повинен перехоплювати `/api/*` (потрібен інтеграційний тест на обидва випадки).

**Neutral**
- Перехід на TanStack Router пізніше торкнеться лише шару `app` і посилань у `pages`/`widgets` (≈1–2 дні).

## Links

- PRD: [[../PRD.md]] AC-09, AC-12, AC-14
- SAD: [[../sad.md]] §4
- Project ADR: [[../../../adr/0001-use-python-fastapi-and-react-vite-stack.md]]
