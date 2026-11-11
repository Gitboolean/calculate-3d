---
id: T24
title: "plastic_not_found: інвалідувати пластики й довести скидання вибору на сторінці виробу"
layer: "ui"
deps: ["T20"]
acs: ["AC-07", "AC-08"]
files_hint: ["web/src/entities/plastic/api/plastics.ts", "web/src/entities/plastic/index.ts", "web/src/pages/calculate/ui/CalculatePage.tsx", "web/src/pages/item/ui/ItemReslice.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx", "web/src/pages/item/ui/ItemPage.reslice.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T24 — plastic_not_found: інвалідувати пластики й довести скидання вибору на сторінці виробу

## Why

Re-review R3: тест F5 на `ItemPage.reslice.test.tsx:177-195` перевіряє лише повідомлення — видалення `onImportedChange(clearRejectedChoice(…))` (`ItemReslice.tsx:68`) лишає все зеленим (DoD T20). R4: `plasticsKey` ніде не інвалідується після `importing.plastic_not_found` (`CalculatePage.tsx:138`, `ItemReslice.tsx:66-69`) — видалений пластик лишається в `NativeSelect`, повтор дає той самий 422. Джерело: [review 2026-11-10 r2](../_review/review-2026-11-10-r2.md).

## What

- Хелпер інвалідації пластиків з `@/entities/plastic` (FSD), виклик в обох onError для `importing.plastic_not_found`.
- ItemPage.reslice: assert select == '' і «Підтвердити» disabled після 422.
- Обидві сторінки: assert опція видаленого пластику зникла.

## Definition of Done

> Після 422 importing.plastic_not_found на CalculatePage і ItemPage.reslice видалений пластик зникає зі списку (запит пластиків інвалідовано), вибір філамента порожній, «Зберегти»/«Підтвердити» вимкнені — це перевіряють тести обох сторінок; make web-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
