---
id: T27
title: "Імпорт у розрахунку: один стан форми й імпорту з функціональними оновленнями"
layer: "ui"
deps: ["T25"]
acs: ["AC-07", "AC-09b"]
files_hint: ["web/src/pages/calculate/ui/CalculatePage.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T27 — Імпорт у розрахунку: один стан форми й імпорту з функціональними оновленнями

## Why

Re-review r3. S2: `parse.mutate(file, { onSuccess })` (`ImportFileButton.tsx:42`) захоплює
`applyImport` з рендеру вибору файлу — після «Скасувати імпорт» під час розбору повторного імпорту
застарілий `imported ≠ null` не робить знімка, рядки файлу заміняють форму й зберігаються без
`filament_mappings`. S4: `onError` збереження (`CalculatePage.tsx:151-154`) захоплює `imported` і після
скасування під час збереження, що впало з 409, повертає скасований імпорт. S5: guard «лише перший
знімок» (`CalculatePage.tsx:46`) не покрито тестом. Джерело:
[review 2026-11-11 r3](../_review/review-2026-11-11-r3.md).

## What

- Тримати `{ value, imported, beforeImport }` в одному `useReducer`/`useState`; кожен крок імпорту, скасування і `clearRejectedChoice` — функціональне оновлення від поточного стану.
- Тести CalculatePage: (1) ручні 120 г → імпорт A → вибір B → «Скасувати» під час розбору B → B завершується → форма 120 г / 115,25 ₴, без `filament_mappings`; (2) 120 г → імпорт A → імпорт B → «Скасувати» → 120 г, 3 год 30 хв, 115,25 ₴, збереження без `filament_mappings`; (3) «Скасувати» під час збереження, що повертає 409 → панель імпорту не повертається.

## Definition of Done

> Три тести CalculatePage (скасування під час розбору повторного імпорту, A → B → скасувати, скасування під час збереження з 409) показують форму до імпорту і збереження без filament_mappings; кожен червоніє на поточному коді; make web-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
