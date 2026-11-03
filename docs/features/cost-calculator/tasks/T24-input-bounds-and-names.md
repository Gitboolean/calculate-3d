---
id: T24
title: "Обмежити масштабовані цілі зверху і нормалізувати імена (NFC, невидимі символи)"
layer: "app"
deps: ["T23"]
acs: ["AC-02", "AC-05", "AC-07", "AC-11"]
files_hint: ["backend/src/calculate3d/core", "backend/src/calculate3d/modules", "backend/tests", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T24 — Обмежити масштабовані цілі зверху і нормалізувати імена (NFC, невидимі символи)

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-02, AC-05, AC-07, AC-11 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Кожне вхідне поле *_kop/_cg/_s/_w/_h має le=-межу, за якої максимальний min_donation_kop ≤ 2^53−1; завеликі значення → 422 validation_error біля поля (integration-тести на pricing/costing/catalog), не 500; normalize_name робить NFC перед trim; ім'я, порожнє після видалення символів категорії Cf, відхиляється; unit-тести в tests/unit/test_text.py; make api-types; make check зелений. Знахідки S2-1, S2-3 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** T23.
