---
id: T29
title: "Зв'язати помилки годин/хвилин через aria-describedby і посилити тести AC-14b та моки quote"
layer: "ui"
deps: ["T28"]
acs: ["AC-07", "AC-14b"]
files_hint: ["web/src/features/quote-form", "web/src/pages/item/ui/ItemPage.test.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T29 — Зв'язати помилки годин/хвилин через aria-describedby і посилити тести AC-14b та моки quote

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-07, AC-14b у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Поля годин і хвилин у QuoteForm мають aria-describedby на показані повідомлення ${id}-hours-error/-minutes-error/-time-error (тест через toHaveAccessibleDescription); ItemPage.test після збереження перевіряє 77,77 ₴ у статусі «Мінімальний донат»; fallback-мок у CalculatePage.test відповідає контракту (нульова розбивка або 500 на неочікуваний ключ); make web-check зелений. Знахідки S2-7, S1-9, S2-9 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** T28.
