---
id: T16
title: "Додати entity quote (debounce + ключ запиту) і віджет cost-breakdown"
layer: "ui"
deps: ["T8", "T13"]
acs: ["AC-06", "AC-06b", "AC-08", "AC-08b"]
files_hint: ["web/src/entities/quote", "web/src/widgets/cost-breakdown"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T16 — Додати entity quote (debounce + ключ запиту) і віджет cost-breakdown

## Why

[ADR-0002](../adr/0002-compute-cost-on-server-only.md) (UI перепитує сервер після паузи, показує лише відповідь для поточних значень); [sad.md](../sad.md) §11 ризик «на екрані лишається ціна для попередніх значень». Критерії: AC-06, AC-06b, AC-08, AC-08b у [PRD §5](../PRD.md).

## What

- `entities/quote`: `useQuote(input | null)` — debounce, `queryKey` = нормалізований вхід; показується лише результат для поточного ключа (без `placeholderData` зі старим донатом).
- `widgets/cost-breakdown`: мінімальний донат + 4 рядки (пластик, електрика, знос, брак) через `format-money`; стан «рахую…»; спільний для `calculate` і `item`.

## Definition of Done

- [ ] Тест гонки відповідей (fake timers + відкладений мок) — на екрані лише донат для останнього входу.
- [ ] Тест віджета: AC-06 (115,25 / 78,00 / 2,27 / 24,50 / 10,48), AC-08b (сума рядків ≠ донату — не «виправляється» на клієнті).
- [ ] `make web-check` зелений.

## Notes

- **Blocked by:** [T8](./T8-costing-quote-endpoint.md), [T13](./T13-web-foundation.md).
- UI нічого не рахує — лише відображає копійки з сервера (ADR-0002).
