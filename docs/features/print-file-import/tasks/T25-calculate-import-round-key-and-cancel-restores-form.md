---
id: T25
title: "Імпорт у розрахунку: key панелі за раундом імпорту і відновлення форми після скасування"
layer: "ui"
deps: ["T20"]
acs: ["AC-07", "AC-09b", "AC-10"]
files_hint: ["web/src/pages/calculate/ui/CalculatePage.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T25 — Імпорт у розрахунку: key панелі за раундом імпорту і відновлення форми після скасування

## Why

Re-review Q6: `key` панелі (`CalculatePage.tsx:90`) — набір філаментів, а не імпорт; повторний імпорт без скасування зберігає `dismissed` (`FilamentMappingPanel.tsx:32`), діалог сумування не відкривається. Q7: «Скасувати імпорт» (`CalculatePage.tsx:94`) скидає лише `imported`, а рядки/час із `quoteFormFrom` лишаються у формі. Джерело: [review 2026-11-10 r2](../_review/review-2026-11-10-r2.md).

## What

- Лічильник `importRound` (як `ItemPage.tsx:71`), інкремент в `onParsed`, ним key панелі.
- Знімок `value` перед імпортом; на «Скасувати імпорт» — відновити його.
- Тести: подвійний імпорт; ready-then-cancel.

## Definition of Done

> Тест CalculatePage: два імпорти того самого файлу з конфліктом знову відкривають діалог сумування; після готового імпорту «Скасувати імпорт» повертає форму до стану перед імпортом (рядки, час, донат) і зберігає без filament_mappings; make web-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
