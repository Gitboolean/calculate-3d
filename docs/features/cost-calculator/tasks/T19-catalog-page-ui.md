---
id: T19
title: "Зібрати сторінку /catalog: пошук за ?q= і список виробів з актуальним мінімальним донатом"
layer: "ui"
deps: ["T11", "T13", "T18"]
acs: ["AC-12", "AC-13"]
files_hint: ["web/src/pages/catalog", "web/src/entities/item"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T19 — Зібрати сторінку /catalog: пошук за ?q= і список виробів з актуальним мінімальним донатом

## Why

[sad.md](../sad.md) §6 «Critical flow 2»; [ADR-0003](../adr/0003-recompute-catalog-prices-on-every-read.md) (ціни завжди з сервера, без кешу між відкриттями); [PRD](../PRD.md) AC-12 / AC-13. Критерії: AC-12, AC-13 у [PRD §5](../PRD.md).

## What

- `entities/item`: `useItems(q)`; `staleTime: 0` — каталог перезапитується при кожному відкритті (AC-13).
- `pages/catalog`: поле пошуку синхронізоване з `?q=` (`useSearchParams`); `Table` з назвою і `format-money(min_donation_kop)`; рядок → `/catalog/:itemId`; порожній стан.
- Порядок і фільтр — як повернув сервер (UI не пересортовує).

## Definition of Done

- [ ] Vitest: AC-12 (`?q=` у URL і в запиті), AC-13 (повторний mount → новий запит, нова ціна).
- [ ] `make web-check` зелений.

## Notes

- **Blocked by:** [T11](./T11-catalog-router-and-plastic-in-use.md), [T13](./T13-web-foundation.md), [T18](./T18-save-item-ui.md).
- Спільна `entities/item` з T18/T20 → черга.
