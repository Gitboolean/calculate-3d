---
id: T41
title: "Рахувати довжину назви як сервер (NFC, code points) і чекати перезапит замість sleep у тесті каталогу"
layer: "ui"
deps: []
acs: ["AC-02", "AC-11", "AC-12"]
files_hint: ["web/src/features/edit-plastic/model/validate.ts", "web/src/features/save-item/model/name.ts", "web/src/pages/catalog/ui/CatalogPage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T41 — Рахувати довжину назви як сервер (NFC, code points) і чекати перезапит замість sleep у тесті каталогу

## Why

Follow-up з рев'ю [review-2026-10-30](../_review/review-2026-10-30.md). Критерії: AC-02, AC-11, AC-12 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] edit-plastic/validate.ts і save-item/name.ts міряють [...name.normalize('NFC').trim()].length; серверний 422 на name показується як «Назва — від 1 до 100 символів» (не «обов'язкова»); тести: 60 емодзі приймаються, 60×U+0344 відхиляються з повідомленням про довжину; CatalogPage.test.tsx:157 замість sleep 400 мс чекає (vi.waitFor) на GET /api/catalog/items без q перед негативними перевірками; make web-check зелений. Знахідки R3-6, R3-7 у docs/features/cost-calculator/_review/review-2026-10-30.md.

## Notes

- **Blocked by:** —.
