---
id: T11
title: "Додати shadcn-примітив dialog у shared/ui"
layer: "ui"
deps: []
acs: ["AC-10"]
files_hint: ["web/src/shared/ui/dialog.tsx", "web/src/shared/ui/index.ts", "web/package.json"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T11 — Додати shadcn-примітив dialog у shared/ui

## Why

Єдиний новий примітив, названий у [sad.md](../sad.md) §4 «UI-architecture»: підтвердження сумування AC-10 і панель «було → стало» — модальні кроки. Решта UI збирається з наявних `button`, `card`, `select`, `table`, `alert-dialog`.

## What

- `npx shadcn add dialog` (або ручне копіювання на тих самих Radix-залежностях, що й `alert-dialog`) у `web/src/shared/ui/dialog.tsx`, стилі — лише Tailwind + токени `app/styles/index.css`.
- Реекспорт з `shared/ui/index.ts`.

## Definition of Done

> shared/ui експортує Dialog, а Vitest-тест показує, що він відкривається, має доступну назву й закривається Escape.

- [ ] `dialog.test.tsx`: відкривається з тригера, `role=dialog` з доступною назвою, Escape закриває
- [ ] `make web-check` зелений (Steiger, Prettier, `tsc`)

## Notes

Не дублювати `alert-dialog`: якщо обидва кроки (AC-10, AC-05) вкладаються в «підтвердити / скасувати», T14/T16 можуть узяти `alert-dialog`, і тоді T11 скасовується — рішення фіксує T14.
