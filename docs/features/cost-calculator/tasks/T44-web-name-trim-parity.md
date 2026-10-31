---
id: T44
title: "Обрізати назву на клієнті так само, як сервер (Cf і пробіли по краях), і записати U+0344 у тестах як escape"
layer: "ui"
deps: []
acs: ["AC-02", "AC-11"]
files_hint: ["web/src/shared/lib/normalize-name.ts", "web/src/features/edit-plastic/model/validate.test.ts", "web/src/features/save-item/model/name.test.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T44 — Обрізати назву на клієнті так само, як сервер (Cf і пробіли по краях), і записати U+0344 у тестах як escape

## Why

Follow-up з рев'ю [review-2026-10-31](../_review/review-2026-10-31.md). Критерії: AC-02, AC-11 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] shared/lib/normalize-name.ts після NFC обрізає по краях ті самі символи, що core/text.py::normalize_name (\s, \p{Cf}, U+001C–U+001F, U+0085), коментар про розбіжність прибрано; тести: 100 літер + U+200B і + U+00AD приймаються як 100 символів, назва лише з U+200B → «Назва обов’язкова» для пластику і виробу; validate.test.ts:54 і name.test.ts:16 використовують '\u0344' з коментарем про розклад NFC; make web-check зелений. Знахідки R4-6, R4-9 у docs/features/cost-calculator/_review/review-2026-10-31.md.

## Notes

- **Blocked by:** —.
