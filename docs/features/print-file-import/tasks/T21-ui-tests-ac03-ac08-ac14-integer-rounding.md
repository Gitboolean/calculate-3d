---
id: T21
title: "UI-тести AC-03/AC-08/AC-14 після імпорту і цілочислове округлення мг → сг"
layer: "ui"
deps: ["T20"]
acs: ["AC-03", "AC-08", "AC-14"]
files_hint: ["web/src/pages/calculate/ui/CalculatePage.test.tsx", "web/src/features/slicer-import/model/compose.ts", "web/src/features/slicer-import/model/compose.test.ts", "docs/features/print-file-import/test-plan.md"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T21 — UI-тести AC-03/AC-08/AC-14 після імпорту і цілочислове округлення мг → сг

## Why

Review F6–F9: web-frontend — target surface, але AC-08 (заміна підставленого пластику, видалення/редагування рядка), ліміт AC-14 після імпорту й округлення грамів AC-03 мають лише model/backend-тести; `compose.ts:56-57` ділить float, хоча ADR 0004 вимагає цілих; test-plan рядок 99 очікує ліміт від compose, а його застосовує форма. Джерело: [review 2026-11-10](../_review/review-2026-11-10.md).

## What

- CalculatePage-тест AC-08: імпорт VTULKA (`plastic_id: 'pla'`) → змінити на `petg` → видалити рядок → зберегти → `filament_mappings: [{…, plastic_id: 'petg'}]`.
- CalculatePage-тест AC-14: `usage_mg: 1_000_000_010` → «Витрата — не більше 1 000 000 г», без донату, «Зберегти в каталог» вимкнено.
- CalculatePage-тест AC-03: `usage_mg: 11543` → «Витрата, г» = `11,55`.
- `compose.ts:56-57`: цілочислове ділення з округленням вгору (`(mg + 9 - ((mg + 9) % 10)) / 10` або BigInt).
- `test-plan.md:99-100`: ліміт застосовує `parseQuoteForm`, не compose.

## Definition of Done

> Три нові CalculatePage-тести (AC-03, AC-08, AC-14) зелені через UI, compose округлює мг → сг без float-ділення, test-plan рядок 99 відповідає коду, а make web-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
