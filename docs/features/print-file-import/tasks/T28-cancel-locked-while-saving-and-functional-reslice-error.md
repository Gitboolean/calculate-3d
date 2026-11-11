---
id: T28
title: "Скасування заблоковане під час збереження; помилка переслайсу — функціональне оновлення"
layer: "ui"
deps: ["T27"]
acs: ["AC-06", "AC-07", "AC-08"]
files_hint: ["web/src/features/slicer-import/ui/WasBecomePanel.tsx", "web/src/pages/item/ui/ItemReslice.tsx", "web/src/pages/item/ui/ItemPage.tsx", "web/src/pages/item/ui/ItemPage.reslice.test.tsx", "web/src/pages/calculate/ui/CalculatePage.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx", "web/src/features/save-item/ui/SaveItemForm.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T28 — Скасування заблоковане під час збереження; помилка переслайсу — функціональне оновлення

## Why

Re-review r4. R5: «Скасувати» у «було → стало» (`WasBecomePanel.tsx:72`) активна під час PUT —
після скасування PUT усе одно переслайсує виріб (80,00 г → 95,00 г після refetch), а помилка PUT
губиться; на `/calculate` «Скасувати імпорт» (`CalculatePage.tsx:127`) активна під час create.
R6: `onError` у `ItemReslice.tsx:71` застосовує `clearRejectedChoice` до імпорту з моменту кліку.
R7b: тест S2 (`CalculatePage.test.tsx:724-726`) з `if (cancel)` не фіксує поведінку; тест S4
(рядок 760) позначено AC-09b замість AC-07. Джерело:
[review 2026-11-11 r4](../_review/review-2026-11-11-r4.md).

## What

- `WasBecomePanel`: «Скасувати» `disabled` під час `isSaving`; `/calculate`: «Скасувати імпорт» `disabled`, поки create у польоті (стан pending зі `SaveItemForm` угору).
- `ItemPage`/`ItemReslice`: помилка збереження — функціональне оновлення від поточного імпорту (`onImportedChange((cur) => clearRejectedChoice(cur, e))`).
- Тести: PUT утримано → «Скасувати» disabled → PUT завершився → панель закрита через `onDone`; те саме для create на `/calculate`; 409 `importing.plastic_not_found` під час PUT не скидає вибір, зроблений для іншого філамента; тест S2 явно перевіряє панель B (VTULKA_B), потім скасування → ручна форма 120 г; тег S4-тесту → AC-07.

## Definition of Done

> «Скасувати» на сторінці виробу і «Скасувати імпорт» у розрахунку недоступні, поки збереження в польоті; 409 під час переслайсу скидає лише відхилений вибір від поточного стану; тест S2 фіксує один результат; кожен новий тест червоніє на поточному коді; make web-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
