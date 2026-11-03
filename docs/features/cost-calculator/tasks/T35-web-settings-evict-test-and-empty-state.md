---
id: T35
title: "Покрити тестом скидання кешу цін після налаштувань і не показувати порожній стан поверх placeholder-даних"
layer: "ui"
deps: []
acs: ["AC-06", "AC-12", "AC-13"]
files_hint: ["web/src/app/layout/AppRoutes.cache.test.tsx", "web/src/pages/catalog/ui/CatalogPage.tsx", "web/src/pages/catalog/ui/CatalogPage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T35 — Покрити тестом скидання кешу цін після налаштувань і не показувати порожній стан поверх placeholder-даних

## Why

Follow-up з рев'ю [review-2026-10-29-r2](../_review/review-2026-10-29-r2.md). Критерії: AC-06, AC-12, AC-13 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] AppRoutes.cache.test.tsx має кейс: зміна тарифу в PriceSettingsSection → у каталозі не видно старого донату до свіжої відповіді (падає без evictPricedQueries у useReplacePriceSettings); CatalogPage не показує «Каталог порожній»/«Нічого не знайдено», поки items.isPlaceholderData; тест: порожній результат ?q=xyz → очищення пошуку до некешованого запиту; make web-check зелений. Знахідки R2-8, R2-9 у docs/features/cost-calculator/_review/review-2026-10-29-r2.md.

## Notes

- **Blocked by:** —.
