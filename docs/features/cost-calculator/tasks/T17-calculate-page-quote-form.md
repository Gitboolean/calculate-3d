---
id: T17
title: "Зібрати сторінку /calculate з формою quote-form, валідацією AC-07 і станом «бракує налаштувань»"
layer: "ui"
deps: ["T14", "T16"]
acs: ["AC-06", "AC-06b", "AC-07", "AC-09"]
files_hint: ["web/src/pages/calculate", "web/src/features/quote-form", "web/src/shared/ui/select.tsx", "web/src/shared/ui/index.ts"]
owner: "Anton Pohorielov"
estimate: "L"
status: "todo"
---

# T17 — Зібрати сторінку /calculate з формою quote-form, валідацією AC-07 і станом «бракує налаштувань»

## Why

[sad.md](../sad.md) §6 «Critical flow 1» (гілки `alt поле хибне`, `alt налаштувань цін бракує`); [PRD](../PRD.md) AC-06, AC-06b, AC-07, AC-09. Критерії: AC-06, AC-06b, AC-07, AC-09 у [PRD §5](../PRD.md).

## What

- `features/quote-form` — керований компонент (`value`/`onChange`): рядки «пластик (select) + грами» з додаванням і видаленням, години + хвилини; клієнтська валідація AC-07 (повтор пластику → «об'єднайте витрату в одному рядку», хвилини ≥ 60, час 0, порожні години = 0); видає `QuoteInput | null`.
- `pages/calculate`: форма + `cost-breakdown`; без пластиків або налаштувань (`usePlastics`, `usePriceSettings`, або `409 costing.settings_missing` з `missing`) — пояснення й посилання на `/settings` замість донату.
- `npx shadcn add select`, якщо нативний `<select>` не підходить стилістично.

## Definition of Done

- [ ] Vitest: AC-06, AC-06b, AC-07 (кожен хибний випадок), AC-09 (обидва варіанти «бракує»).
- [ ] `quote-form` не залежить від сторінки (його використовує T20).
- [ ] `make web-check` зелений.

## Notes

- **Blocked by:** [T14](./T14-settings-plastics-ui.md), [T16](./T16-quote-entity-and-breakdown-widget.md).
- `entities/plastic` з T14 перевикористовується, а не дублюється. `shared/ui/index.ts` спільний з T14 → черга.
