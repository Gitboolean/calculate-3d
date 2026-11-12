---
id: T15
title: "Сторінка розрахунку: імпорт у форму і передача зіставлень під час збереження виробу"
layer: "ui"
deps: ["T9", "T14"]
acs: ["AC-01", "AC-02", "AC-07", "AC-08", "AC-14"]
files_hint: ["web/src/pages/calculate/ui/", "web/src/features/save-item/", "web/src/features/quote-form/"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T15 — Сторінка розрахунку: імпорт у форму і передача зіставлень під час збереження виробу

## Why

Critical flow 1 і Flow 6 [sad.md](../sad.md) §6; `save-item` передає зіставлення ([ADR 0003](../adr/0003-remember-filament-mappings-in-the-item-save-transaction.md)). AC-01 (заміна рядків, ручні правки, збереження), AC-07/AC-08 (запам'ятати лише при збереженні) у [PRD §5](../PRD.md).

## What

- `pages/calculate/ui/CalculatePage.tsx`: `ImportFileButton` + `FilamentMappingPanel`; готові рядки → `quoteFormFrom(...)` замінює всю форму (і попередній імпорт); показ імпортованої пластини.
- `features/quote-form`: прийняти зовнішнє значення форми без втрати ручного редагування (якщо поточний API цього не дає).
- `features/save-item`: проп `filamentMappings?: FilamentMappingInput[]` → у тіло `createItem`.
- Помилки меж рядків (32 / 1 000 000 г) показує наявний `QuoteError` з відповіді `quoteCost` (AC-14).

## Definition of Done

> Vitest-тест CalculatePage показує, що імпорт vtulka_A замінює всі рядки й час (1 год 38 хв), показує донат з quoteCost, ручна правка після імпорту працює, а збереження виробу надсилає filament_mappings з вибором кожного філамента; без збереження зіставлення не надсилаються.

- [ ] Тест сторінки: попередні ручні рядки замінено, повторний імпорт замінює попередній (AC-01)
- [ ] Тест: збереження → тіло `createItem` містить `filament_mappings`; без збереження — жодного запиту з ними (AC-07)
- [ ] Наявні тести `CalculatePage`, `SaveItemForm` зелені; `make web-check` зелений

## Notes

Ділить `features/save-item` і `features/quote-form` з T16 — одна смуга. Сторінка — єдине місце, що з'єднує `slicer-import` і `quote-form` (FSD).
