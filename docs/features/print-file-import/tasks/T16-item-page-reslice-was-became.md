---
id: T16
title: "Сторінка виробу: імпорт перенарізки з «було → стало», підтвердженням і скасуванням"
layer: "ui"
deps: ["T15"]
acs: ["AC-05", "AC-06", "AC-07", "AC-08"]
files_hint: ["web/src/pages/item/ui/", "web/src/features/slicer-import/ui/WasBecomePanel.tsx", "web/src/features/save-item/"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T16 — Сторінка виробу: імпорт перенарізки з «було → стало», підтвердженням і скасуванням

## Why

Critical flow 2 [sad.md](../sad.md) §6; «було» — свіжий `GET` виробу ([sad.md](../sad.md) §5). AC-05 (diff і перерахунок), AC-06 (скасування — без змін), AC-07/AC-08 (зіставлення разом із підтвердженням) у [PRD §5](../PRD.md).

## What

- `features/slicer-import/ui/WasBecomePanel.tsx`: рядки з `diffItem` (T12) + донат «було → стало», дії «Підтвердити» / «Скасувати».
- `pages/item/ui/ItemEditor.tsx` / `ItemPage.tsx`: імпорт робить `refetch` виробу (незбережені правки відкидаються), «стало» рахує `quoteCost`; ручні правки до підтвердження перераховують «стало» (AC-14b/14c етапу 1).
- Підтвердження → `updateItem` з рядками, часом і `filament_mappings`, назва незмінна; скасування / відмова файлу → форма й каталог як були.

## Definition of Done

> Vitest-тест ItemPage показує для «Підставки» «було → стало» 80 → 95 г, PETG прибрано, 2:00 → 2:15, 80,63 → 60,73 ₴ з «було» зі свіжого getItem, перерахунок «стало» після ручної правки, а скасування чи відмова файлу не надсилає updateItem.

- [ ] Тест AC-05 з числами PRD; тест AC-06: «Скасувати» → жодного `PUT`
- [ ] Тест: незбережена ручна правка до імпорту не потрапляє в «було»
- [ ] Наявні тести `ItemPage` зелені; `make web-check` зелений

## Notes

Ділить `features/save-item` з T15 — тому `deps: [T15]`. Після цієї задачі можна прогнати `/sdlc:verify-ui print-file-import` на живому застосунку.
