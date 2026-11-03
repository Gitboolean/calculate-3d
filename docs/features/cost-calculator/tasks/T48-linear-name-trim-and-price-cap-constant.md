---
id: T48
title: "Обрізати назву лінійно, як сервер, і будувати текст межі ціни з однієї константи"
layer: "ui"
deps: []
acs: ["AC-02", "AC-11"]
files_hint: ["web/src/shared/lib/normalize-name.ts", "web/src/shared/lib/normalize-name.test.ts", "web/src/features/edit-plastic/model/validate.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T48 — Обрізати назву лінійно, як сервер, і будувати текст межі ціни з однієї константи

## Why

Follow-up з рев'ю [review-2026-10-31-r5](../_review/review-2026-10-31-r5.md). Критерії: AC-02, AC-11 у [PRD §5](../PRD.md).

## Definition of Done

- [x] shared/lib/normalize-name.ts після NFC обрізає краї двома індексами по code points з тестом одного символу [\s\p{Cf}\u001c-\u001f\u0085] (як core/text.py::normalize_name), без глобального regex з якорем $; тест: 'a' + 100 000 пробілів + 'b' нормалізується менш ніж за 50 мс і зберігає внутрішні пробіли; наявні тести normalize-name.test.ts зелені без змін; edit-plastic/model/validate.ts: «10 000 000» з'являється один раз (одна константа межі ціни, з якої будуються PRICE_TOO_LARGE і PRICE_RANGE, або вивід з MAX_PRICE_KOP), тексти повідомлень незмінні; make web-check зелений. Знахідки R5-5, R5-7 у docs/features/cost-calculator/_review/review-2026-10-31-r5.md.

## Notes

- **Blocked by:** —.
