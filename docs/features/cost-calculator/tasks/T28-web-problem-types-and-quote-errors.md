---
id: T28
title: "Типізувати problem-розширення зі згенерованих схем і показувати помилки quote на обох екранах"
layer: "ui"
deps: ["T23", "T27"]
acs: ["AC-07", "AC-09", "AC-14"]
files_hint: ["web/src/shared/api", "web/src/widgets/cost-breakdown", "web/src/features/quote-form", "web/src/pages/calculate", "web/src/pages/item"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T28 — Типізувати problem-розширення зі згенерованих схем і показувати помилки quote на обох екранах

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-07, AC-09, AC-14 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] shared/api/errors.ts будує Problem зі згенерованих FieldProblem/PlasticInUseProblem/SettingsMissingProblem/ValidationProblem, MISSING_TEXT типізовано enum'ом missing; спільна панель результату quote (MissingSettings / costing.plastic_not_found «Один із пластиків уже видалено…» / нейтральний текст для 5xx і мережі) використовується на /calculate і в ItemEditor (кнопка збереження вимкнена при помилці); ItemPage показує помилку, якщо не завантажились пластики, а MissingSettings — усередині секції з заголовком; component-тести на кожну гілку; make web-check зелений. Знахідки S1-8, S2-4, S2-5, S2-6 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** T23, T27.
