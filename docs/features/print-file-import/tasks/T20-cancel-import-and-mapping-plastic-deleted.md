---
id: T20
title: "Скасування імпорту в розрахунку і пояснення importing.plastic_not_found під час збереження"
layer: "ui"
deps: ["T15", "T16"]
acs: ["AC-07", "AC-08", "AC-09b"]
files_hint: ["web/src/pages/calculate/ui/CalculatePage.tsx", "web/src/features/slicer-import/ui/FilamentMappingPanel.tsx", "web/src/features/save-item/model/name.ts", "web/src/pages/item/ui/ItemReslice.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx", "web/src/pages/item/ui/ItemPage.reslice.test.tsx"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T20 — Скасування імпорту в розрахунку і пояснення importing.plastic_not_found під час збереження

## Why

Review F4: `imported` у `CalculatePage.tsx` ніколи не скидається — незіставлений імпорт блокує ручний розрахунок (AC-09b «розпочатий імпорт не зберігається»), а зіставлення покинутого файлу надсилаються з пізнішим збереженням (AC-07). Review F5: `saveError` (`save-item/model/name.ts:16-26`) не знає `importing.plastic_not_found` (SAD §6 Flow 6) — повтор падає так само. Джерело: [review 2026-11-10](../_review/review-2026-11-10.md).

## What

- Дія «Скасувати імпорт» (FilamentMappingPanel / CalculatePage) → `setImported(null)`; `key` панелі за імпортом, щоб локальний `dismissed` не переходив на наступний файл.
- `saveError`: гілка `importing.plastic_not_found` з українським поясненням («Пластик, обраний для філамента з файлу, уже видалено — оберіть інший»); скинути вибір цього філамента (за `field` `filament_mappings.N.plastic_id`) й інвалідувати запит пластиків.
- Те саме в `ItemReslice.tsx:63`.

## Definition of Done

> Тести CalculatePage показують, що після скасування незіставленого імпорту ручні рядки дають донат і зберігаються без filament_mappings, а 422 importing.plastic_not_found дає українське пояснення й знову просить обрати пластик (CalculatePage і ItemPage.reslice); make web-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
