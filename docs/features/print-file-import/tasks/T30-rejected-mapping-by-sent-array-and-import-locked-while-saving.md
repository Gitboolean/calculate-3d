---
id: T30
title: "Відхилений маппінг розв'язується за надісланим масивом; імпорт заблоковано під час збереження"
layer: "ui"
deps: ["T28", "T29"]
acs: ["AC-07", "AC-08", "AC-13"]
files_hint: ["web/src/features/slicer-import/model/state.ts", "web/src/pages/calculate/ui/CalculatePage.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx", "web/src/pages/item/ui/ItemReslice.tsx", "web/src/pages/item/ui/ItemPage.tsx", "web/src/pages/item/ui/ItemPage.reslice.test.tsx", "web/src/features/slicer-import/ui/ImportFileButton.tsx", "backend/tests/unit/test_importing_archive_budget.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T30 — Відхилений маппінг розв'язується за надісланим масивом; імпорт заблоковано під час збереження

## Why

Re-review r5. R9: `clearRejectedChoice` (`state.ts:39-44`) перераховує `chosen` з поточного стану,
а індекс `filament_mappings.<i>` адресує масив, надісланий у момент кліку. Якщо під час
POST/PUT вибір змінився (філамент скинуто на «Оберіть пластик» або реімпортовано інший файл),
очищується не той філамент. «Імпортувати файл» (`CalculatePage.tsx:121`, `ItemPage.tsx:68`)
активна під час збереження; на `/item` реімпорт ремаунтить `ItemReslice` (`key={importRound}`),
і помилка PUT для файлу A губиться. R10: тест R7b (`CalculatePage.test.tsx:725-731`) не перевіряє,
що перше скасування спрацювало, і не відрізняє B від A (обидва `PLA`). R11: accept-тест на
`MAX_CD_BYTES` (`test_importing_archive_budget.py:73`) викликає лише `_check_central_directory`.
Джерело: [review 2026-11-11 r5](../_review/review-2026-11-11-r5.md).

## What

- `clearRejectedChoice` отримує надісланий масив (`mappingsFor(...)` з моменту кліку): ключ = `filamentKey(sent[i])`; очищувати, лише якщо поточний `choice[key] === sent[i].plastic_id`, інакше стан без змін. Обидві сторінки передають надісланий масив.
- `ImportFileButton` `disabled`, поки create (`useIsCreatingItem()`) / update (`update.isPending`) у польоті — на `/calculate` і `/item`.
- Тести: PROBE1 (під час POST скинути #3F8E43, 422 на індекс 0 → `petg` у #000000 лишається); PROBE2 (кнопка імпорту disabled під час POST/PUT); аналог для `/item`.
- R10: після першого «Скасувати імпорт» — region «Філаменти з файлу» відсутній; після `release()` — `19,00 ₴` (котирування B). Мутант «cancel disabled під час parse» має червоніти.
- R11: accept-тест додатково перевіряє, що `parser.read_sliced_plate(body)` повертається без помилки.

## Definition of Done

> 422 `filament_mappings.<i>` очищує лише той філамент, що був i-м у надісланому масиві, і лише якщо він досі тримає той самий пластик; «Імпортувати файл» недоступна, поки збереження в польоті, на обох сторінках; тест R7b фіксує зникнення панелі і котирування B; accept-тест на межі проходить повний парсинг; кожен новий тест червоніє на поточному коді; `make check` зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
