---
id: T27
title: "Не показувати донат за старими цінами з кешу і не блимати списком під час пошуку"
layer: "ui"
deps: []
acs: ["AC-06", "AC-12", "AC-13"]
files_hint: ["web/src/entities/quote", "web/src/entities/item", "web/src/entities/plastic", "web/src/entities/price-settings", "web/src/pages/catalog"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T27 — Не показувати донат за старими цінами з кешу і не блимати списком під час пошуку

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-06, AC-12, AC-13 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Успішні мутації plastic і price-settings прибирають кеш ['quote'] та інвалідовують ['items']; повторне відкриття /catalog або того самого quote після зміни ціни ніколи не показує старий донат (тест AC-13 перевіряє, що 115,25 ₴ не з'являється після reopen); useItems має placeholderData keepPreviousData і debounced q у ключі — таблиця не зникає між натисканнями; make web-check зелений. Знахідки S1-2, S2-8 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** —.
