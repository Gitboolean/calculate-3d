---
id: T18
title: "Додати збереження розрахунку в каталог (feature save-item) на /calculate"
layer: "ui"
deps: ["T11", "T17"]
acs: ["AC-10", "AC-11"]
files_hint: ["web/src/features/save-item", "web/src/entities/item", "web/src/pages/calculate"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T18 — Додати збереження розрахунку в каталог (feature save-item) на /calculate

## Why

[sad.md](../sad.md) §6 «Зберегти виріб у каталог»; [PRD](../PRD.md) AC-10 / AC-11; операція `createItem` у [openapi.yaml](../contracts/openapi.yaml). Критерії: AC-10, AC-11 у [PRD §5](../PRD.md).

## What

- `entities/item`: `useCreateItem` (+ базові ключі запитів для каталогу).
- `features/save-item`: поле назви + «Зберегти в каталог»; кнопка неактивна, поки донат не показано; `409 catalog.name_taken` / `422` назви → помилка біля поля; успіх → перехід на `/catalog/:itemId`.

## Definition of Done

- [ ] Vitest: AC-10 (тіло `createItem` = поточні `plastics` + `print_time_s` + назва, без ціни), AC-11 (порожня / зайнята назва).
- [ ] `make web-check` зелений.

## Notes

- **Blocked by:** [T11](./T11-catalog-router-and-plastic-in-use.md), [T17](./T17-calculate-page-quote-form.md).
- `entities/item` далі розширюють T19 і T20 → спільна черга.
