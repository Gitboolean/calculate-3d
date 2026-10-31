---
id: T45
title: "Не показувати межу часу поверх помилки хвилин і будувати тексти меж з констант"
layer: "ui"
deps: ["T44"]
acs: ["AC-02", "AC-07"]
files_hint: ["web/src/features/quote-form/model/parse.ts", "web/src/features/edit-plastic/model/validate.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T45 — Не показувати межу часу поверх помилки хвилин і будувати тексти меж з констант

## Why

Follow-up з рев'ю [review-2026-10-31](../_review/review-2026-10-31.md). Критерії: AC-02, AC-07 у [PRD §5](../PRD.md).

## Definition of Done

- [x] quote-form/model/parse.ts перевіряє загальний час лише коли години і хвилини валідні (хвилини < 60) — для хвилин 99999999999999999999 і 6000001 одне повідомлення біля хвилин (тест); тексти меж у edit-plastic/model/validate.ts і quote-form/model/parse.ts — одна константа на межу (або будуються з MAX_PRICE_KOP / MAX_USAGE_CG / MAX_PRINT_TIME_S) і використовуються і в мапі причин parseDecimal, і в перевірці діапазону; наявні тести повідомлень зелені без змін тексту; make web-check зелений. Знахідки R4-7, R4-8 у docs/features/cost-calculator/_review/review-2026-10-31.md.

## Notes

- **Blocked by:** T44.
