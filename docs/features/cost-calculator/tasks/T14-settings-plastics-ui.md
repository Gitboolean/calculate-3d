---
id: T14
title: "Зібрати розділ пластиків на /settings: список, додавання, редагування, видалення з підтвердженням"
layer: "ui"
deps: ["T7", "T13"]
acs: ["AC-01", "AC-02", "AC-03"]
files_hint: ["web/src/pages/settings", "web/src/features/edit-plastic", "web/src/entities/plastic", "web/src/shared/ui/alert-dialog.tsx", "web/src/shared/ui/index.ts"]
owner: "Anton Pohorielov"
estimate: "L"
status: "done"
---

# T14 — Зібрати розділ пластиків на /settings: список, додавання, редагування, видалення з підтвердженням

## Why

[PRD](../PRD.md) AC-01–AC-03; [sad.md](../sad.md) §6 «Додати або змінити пластик», «Critical flow 3»; §8 «Delete confirmation», «Internationalisation» (текст помилки з `code` + `field`/`items`). Критерії: AC-01, AC-02, AC-03 у [PRD §5](../PRD.md).

## What

- `entities/plastic`: TanStack Query хуки (`usePlastics`, `useCreatePlastic`, `useUpdatePlastic`, `useDeletePlastic`) над `@/shared/api`; інвалідація списку.
- `features/edit-plastic`: форма назва + ціна за кг (`parse-decimal`, scale 2); помилка біля поля з `validation_error` / `pricing.name_taken`.
- Видалення з підтвердженням: `npx shadcn add alert-dialog` (у `shared/ui/`); `409 pricing.plastic_in_use` → повідомлення з переліком `items`.
- Повторно використати `Table`, `Input`, `Label`, `Button`, `Card`.

## Definition of Done

- [ ] Vitest + Testing Library: AC-01, AC-02 (порожня назва, «649,995», 409 name_taken), AC-03 (409 → «Підставка», «Органайзер»), скасування підтвердження нічого не видаляє.
- [ ] Увесь текст українською; назви рендеряться як текст.
- [ ] `make web-check` зелений.

## Notes

- **Blocked by:** [T7](./T7-pricing-router.md), [T13](./T13-web-foundation.md).
- `alert-dialog` потрібен також у T20; його створює саме ця задача. Справжній 409 з `items` бекенд віддає після T11; тест тут використовує мок за контрактом.
