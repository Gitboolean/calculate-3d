---
id: T12
title: "features/slicer-import/model: compose.ts — рядки з точних мг, конфлікти сумування, diff «було → стало»"
layer: "domain"
deps: ["T8"]
acs: ["AC-03", "AC-05", "AC-09", "AC-10", "AC-14"]
files_hint: ["web/src/features/slicer-import/model/", "web/src/features/slicer-import/index.ts"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T12 — features/slicer-import/model: compose.ts — рядки з точних мг, конфлікти сумування, diff «було → стало»

## Why

[ADR 0004](../adr/0004-compose-quote-rows-in-the-web-from-exact-milligrams.md) (чиста TS-функція поруч із формою); Flow 5 [sad.md](../sad.md) §6. AC-03 (сума мг, вгору лише сума), AC-09 (блок без пластику), AC-10 (питати про сумування), AC-05 (diff) у [PRD §5](../PRD.md).

## What

- `compose.ts`: `compose(filaments, choice, confirmedMerges) → { kind: 'ready', rows: {plastic_id, usage_cg}[], print_time_s } | { kind: 'unmapped', filaments } | { kind: 'merge-conflict', groups }`. Групує за обраним пластиком, додає `usage_mg` (BigInt не потрібен: ≤ 2^53−1, контракт), `usage_cg = ceil(sum / 10)`.
- `mappingsFor(filaments, choice)` — `FilamentMappingInput[]` для кожного філамента з вибором, навіть якщо рядок потім видалено (AC-08).
- `diff.ts`: `diffItem(saved: Item, next) →` рядки «було → стало» за пластиками (+ прибрано / додано) і часом.
- Типи — лише з `@/shared/api` (`schema.d.ts`), не вручну.

## Definition of Done

> Vitest compose.test.ts показує 11 543 мг → 1 155 сг, 2 001 + 2 001 мг → 401 сг, незіставлений філамент блокує результат, дві різні пари на один пластик без підтвердження дають конфлікт, а diff «Підставки» дає 80 → 95 г, PETG прибрано, 2:00 → 2:15.

- [ ] `compose.test.ts`: приклади AC-03 і AC-10 з [sad.md](../sad.md) §10 QG-1; однакові дані → той самий результат, що й у бекенд-тесті T10
- [ ] `diff.test.ts`: приклад AC-05 «Підставка»
- [ ] `make web-check` зелений

## Notes

Модель не імпортує `features/quote-form` (FSD забороняє feature → feature): результат — `{plastic_id, usage_cg}[]` + `print_time_s`, а сторінка перетворює його через `quoteFormFrom` (T15). Межі 32 / 1 000 000 г перевіряє `costing` на сервері (AC-14).
