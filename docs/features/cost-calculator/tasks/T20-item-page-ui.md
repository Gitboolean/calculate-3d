---
id: T20
title: "Зібрати сторінку /catalog/:itemId: перегляд, редагування через quote-form і видалення"
layer: "ui"
deps: ["T17", "T18"]
acs: ["AC-14", "AC-14b", "AC-14c", "AC-15"]
files_hint: ["web/src/pages/item", "web/src/features/delete-item", "web/src/entities/item"]
owner: "Anton Pohorielov"
estimate: "L"
status: "done"
---

# T20 — Зібрати сторінку /catalog/:itemId: перегляд, редагування через quote-form і видалення

## Why

[sad.md](../sad.md) §6 «Відкрити виріб», «Зберегти виріб (редагування)», «Видалити виріб»; [PRD](../PRD.md) AC-14–AC-15; операції `getItem`, `updateItem`, `deleteItem`. Критерії: AC-14, AC-14b, AC-14c, AC-15 у [PRD §5](../PRD.md).

## What

- `entities/item`: `useItem(id)`, `useUpdateItem`, `useDeleteItem`.
- `pages/item`: параметри + `cost-breakdown` з `ItemDetail.quote`; режим редагування — назва + `quote-form` з живим `useQuote`; збереження → `updateItem`; 422/409 → помилки біля полів, виріб не змінено (AC-14c). 404 → «Виріб не знайдено».
- `features/delete-item`: `alert-dialog` з T14; підтвердження → `deleteItem` → `/catalog`; скасування нічого не робить.

## Definition of Done

- [ ] Vitest: AC-14, AC-14b, AC-14c, AC-15 (обидві гілки підтвердження).
- [ ] Пряме відкриття `/catalog/<id>` працює (разом із T4 — перевірити вручну в `make run`).
- [ ] `make web-check` зелений.

## Notes

- **Blocked by:** [T17](./T17-calculate-page-quote-form.md), [T18](./T18-save-item-ui.md).
- Перевикористовує `quote-form` (T17), `cost-breakdown` (T16), `alert-dialog` (T14) — нових примітивів не створює.
