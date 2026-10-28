---
id: T15
title: "Зібрати форму налаштувань цін на /settings: 6 полів, одне збереження, знос за годину"
layer: "ui"
deps: ["T7", "T13", "T14"]
acs: ["AC-04", "AC-05"]
files_hint: ["web/src/pages/settings", "web/src/features/edit-price-settings", "web/src/entities/price-settings"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T15 — Зібрати форму налаштувань цін на /settings: 6 полів, одне збереження, знос за годину

## Why

[PRD](../PRD.md) AC-04 / AC-05; [sad.md](../sad.md) §6 «Зберегти налаштування цін»; [ADR-0004](../adr/0004-exchange-quantities-as-scaled-integers.md) (масштаби `kop`, `w`, `h`, `permille`). Критерії: AC-04, AC-05 у [PRD §5](../PRD.md).

## What

- `entities/price-settings`: `usePriceSettings`, `useReplacePriceSettings`.
- `features/edit-price-settings`: тариф, потужність, ціна принтера, термін служби, деталі, брак; клієнтські межі й точність з AC-05; одна кнопка «Зберегти»; будь-яка помилка → нічого не відправляється; 422 з сервера → помилки біля полів.
- Показ `wear_per_hour_kop` через `format-money` (AC-04: 7,00 ₴).

## Definition of Done

- [ ] Vitest: AC-04, AC-05 (порожнє, «4,3216», «7,25», «152,5», термін 0, брак 101 %) → помилки біля кожного хибного поля, жодного запиту.
- [ ] `make web-check` зелений.

## Notes

- **Blocked by:** [T7](./T7-pricing-router.md), [T13](./T13-web-foundation.md), [T14](./T14-settings-plastics-ui.md).
- Спільна `pages/settings` з T14 → одна черга (T14 першим).
