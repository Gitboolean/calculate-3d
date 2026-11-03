---
id: T13
title: "Підключити React Router, оболонку з навігацією, parse-decimal і format-money"
layer: "ui"
deps: []
acs: ["AC-01", "AC-02", "AC-05", "AC-07", "AC-09"]
files_hint: ["web/package.json", "web/package-lock.json", "web/src/app/App.tsx", "web/src/app/layout", "web/src/shared/lib/parse-decimal.ts", "web/src/shared/lib/parse-decimal.test.ts", "web/src/shared/lib/format-money.ts", "web/src/shared/lib/format-money.test.ts", "web/src/shared/lib/index.ts", "web/src/pages"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T13 — Підключити React Router, оболонку з навігацією, parse-decimal і format-money

## Why

[ADR-0001](../adr/0001-route-spa-screens-with-react-router.md) (BrowserRouter, declarative mode, маршрути `/settings`, `/calculate`, `/catalog`, `/catalog/:itemId`); [ADR-0004](../adr/0004-exchange-quantities-as-scaled-integers.md) і [sad.md](../sad.md) §8 «Input parsing»; §10 «Локалізація»; §11 ризик «UI-парсер — єдиний захист від зайвої точності». Критерії: AC-01, AC-02, AC-05, AC-07, AC-09 у [PRD §5](../PRD.md).

## What

- `npm i react-router` (точна версія в lock); `App.tsx`: `BrowserRouter` + `Routes`; `/` → `/calculate`; сторінки-заглушки `settings`, `calculate`, `catalog`, `item` у `pages/` (кожна з `index.ts`).
- Оболонка з навігацією українською з наявних `Button`/`Card` (shadcn) і токенів `index.css`; прецедент — `pages/home/`.
- `shared/lib/parse-decimal(input, scale)`: кома або крапка, trim; зайва точність, не число → помилка з причиною (без округлення); повертає ціле в одиниці (`kop`, `cg`, `permille`).
- `shared/lib/format-money(kop)` — `Intl.NumberFormat('uk-UA', {style:'currency', currency:'UAH'})`.

## Definition of Done

- [ ] `parse-decimal.test.ts`: «650» і «650,00» → 65000; «4,32» / «4.32» → 432; «649,995» → помилка; «7,25» з scale 1 → помилка; «152,5» з scale 0 → помилка; «abc», «» → помилка; від'ємні розпізнаються (межі перевіряє форма).
- [ ] `format-money.test.ts`: 11525 → `115,25 ₴` (з нерозривним пробілом від `Intl`).
- [ ] Навігація між 4 маршрутами працює в component-тесті (`MemoryRouter`).
- [ ] `make web-check` зелений (ESLint, Prettier, Steiger, tsc, vitest, build).

## Notes

- **Blocked by:** —.
- Frontend-гілка стартує з першого дня паралельно з бекендом. Нових UI-примітивів тут не створювати.
