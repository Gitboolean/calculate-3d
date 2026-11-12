---
id: T31
title: "Збереження заблоковане, поки парситься файл; тест /item на надісланий масив"
layer: "ui"
deps: ["T30"]
acs: ["AC-06", "AC-08"]
files_hint: ["web/src/features/slicer-import/api/parse.ts", "web/src/features/slicer-import/index.ts", "web/src/pages/item/ui/ItemPage.tsx", "web/src/pages/item/ui/ItemReslice.tsx", "web/src/pages/item/ui/ItemPage.reslice.test.tsx", "web/src/pages/calculate/ui/CalculatePage.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T31 — Збереження заблоковане, поки парситься файл; тест /item на надісланий масив

## Why

Re-review r6. R12: T30 блокує «Імпортувати файл», поки create/update у польоті, але парсинг,
що стартував **до** «Підтвердити», не блокує Confirm. Коли він завершується під час PUT,
`importFile` (`ItemPage.tsx:32-37`) збільшує `importRound`, і `ItemReslice` ремаунтиться
(`key={importRound}`, `ItemPage.tsx:69-72`), а колбеки `update.mutate` губляться. Probe-тест r6:
при 422 `filament_mappings.0.plastic_id` помилку не показано, а #FFFFFF лишається на видаленому
`pla`; при успіху `onDone` губиться, і панель файлу B лишається, хоча виріб оновлено з A. На
`/calculate` таке саме вікно (`CalculatePage.tsx:174`: Save доступний, поки парсинг у польоті), але
без ремаунту, тож там B лише з'являється після збереження A. R13: мутант M7 (`ItemReslice.tsx:75`
перебудовує масив з поточного стану замість `sent`) проходить усі тести `/item`; тест R6
перевибирає #000000, і індекс 0 при цьому не змінюється.
Джерело: [review 2026-11-11 r6](../_review/review-2026-11-11-r6.md).

## What

- `useParseSlicerFile` отримує `mutationKey` (наприклад `['slicer-import','parse']`); з
  `features/slicer-import` експортується `useIsParsingSlicerFile()` (`useIsMutating` за цим ключем).
- `/item`: «Підтвердити» недоступна, поки парсинг у польоті (`canConfirm`/`isSaving`).
- `/calculate`: «Зберегти» недоступне, поки парсинг у польоті.
- Тести: парсинг на паузі → Confirm/Save disabled; після release Confirm знову доступна, і результат
  PUT з 422 показує помилку та очищує вибір.
- R13: `/item`-двійник тесту R9 з CalculatePage. Під час PUT на паузі скинути #FFFFFF на «Оберіть
  пластик», відповісти 422 на індекс 0, перевірити, що #000000 лишається `petg`. Мутант M7 має
  червоніти.

## Definition of Done

> Поки парсинг у польоті, збереження недоступне на обох сторінках, тож відповідь PUT/POST не може
> загубитися через ремаунт; на `/item` тест фіксує, що індекс відхиленого маппінгу береться з
> надісланого масиву; кожен новий тест червоніє на поточному коді; `make check` зелений.

- [x] Спершу червоний тест, що відтворює знахідку
- [x] `make check` зелений
