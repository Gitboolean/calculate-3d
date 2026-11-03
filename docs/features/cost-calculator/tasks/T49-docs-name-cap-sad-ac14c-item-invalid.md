---
id: T49
title: "Дописати межу назви в SAD, межі в AC-14c, ItemInvalid і 422 каталогу та розвести кейси test-plan за файлами"
layer: "docs"
deps: ["T46", "T47"]
acs: ["AC-02", "AC-07", "AC-11", "AC-14c"]
files_hint: ["docs/features/cost-calculator/sad.md", "docs/features/cost-calculator/PRD.md", "docs/features/cost-calculator/contracts/openapi.yaml", "backend/src/calculate3d/modules/catalog/router.py", "docs/features/cost-calculator/contracts/api-sync-report.md", "docs/features/cost-calculator/test-plan.md", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T49 — Дописати межу назви в SAD, межі в AC-14c, ItemInvalid і 422 каталогу та розвести кейси test-plan за файлами

## Why

Follow-up з рев'ю [review-2026-10-31-r5](../_review/review-2026-10-31-r5.md). Критерії: AC-02, AC-07, AC-11, AC-14c у [PRD §5](../PRD.md).

## Definition of Done

- [x] sad.md: потоки пластику (:208, :215) і збереження виробу (:359) мають гілку «назва довша за 100 символів» на UI і сервері, кроки :211, :356 — «NFC, обрізає пробіли й невидимі символи на краях», рядки покриття :515, :526 оновлено; PRD.md AC-14c перелічує межі AC-07 (1 000 000 г, 100 000 год, 32 пластики) і назву понад 100 символів (або посилається на всі правила AC-07 / AC-11); openapi.yaml ItemInvalid і опис 422 у catalog/router.py називають ті самі межі, що quoteCost, + make api-types; api-sync-report.md — запис reconcile, Verdict PASS або PASS (with deferrals); test-plan.md:46,85 — рівень unit + component + integration, кожен кейс прив'язано до файлу, який його справді містить; make check зелений. Знахідки R5-1, R5-3, R5-4 у docs/features/cost-calculator/_review/review-2026-10-31-r5.md.

## Notes

- **Blocked by:** T46, T47.
