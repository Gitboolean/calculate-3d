---
id: T33
title: "«Змінити» на /item недоступне, поки імпортується файл; тест вікна read-back"
layer: "ui"
deps: ["T32"]
acs: ["AC-05", "AC-06"]
files_hint: ["web/src/pages/item/ui/ItemPage.tsx", "web/src/pages/item/ui/ItemPage.reslice.test.tsx"]
owner: "Anton Pohorielov"
estimate: "XS"
status: "todo"
---

# T33 — «Змінити» на /item недоступне, поки імпортується файл; тест вікна read-back

## Why

Re-review r8, R15 + R16. T32 заблокувала «Зберегти зміни» в `ItemEditor` через `importing`
(парсинг ‖ read-back, `ItemPage.tsx:37,100`), але тест R14 (`ItemPage.reslice.test.tsx:440`)
тримає лише парсинг.

- **R15:** у вікні read-back (парсинг завершився, GET виробу ще в польоті) блокування нічим не
  перевірене. Мутант `importing={importing && !reading}` лишає всі 28 тестів /item зеленими, хоча
  probe r8 показав: під ним «Зберегти зміни» доступна, іде 1 PUT, а коли read-back приходить,
  `ItemReslice` займає тернарник (`ItemPage.tsx:83`), `ItemEditor` розмонтовується і колбеки PUT
  губляться. Це знову R14, у вікні, для якого існує прапорець `reading`.
- **R16:** `importFile` викликає `setEditing(false)` один раз, до `await item.refetch()`
  (`ItemPage.tsx:41`). «Змінити» (`:132`) ніколи не disabled, тож клік під час refetch ставить
  `editing=true`. Після «Скасувати» чи «Підтвердити» панелі імпорту (`onDone` лише
  `setImported(null)`) знову відкривається форма «Змінити виріб», яку користувач не відкривав.
  Дані не губляться.

Джерело: [review 2026-11-11 r8](../_review/review-2026-11-11-r8.md).

## What

- «Змінити» `disabled={importing}`. Це закриває R16 і робить вікно R15 недосяжним через UI.
- Тест (як R12 read-gate, `ItemPage.reslice.test.tsx:377`): `readGate` тримає GET після
  парсингу → «Змінити» недоступна, 0 PUT; після release і закриття панелі форма «Змінити виріб»
  не відкрита.
- Тест R15 має вбивати мутант `importing && !reading` (захист у глибину для `ItemEditor`, якщо
  редактор був відкритий до старту імпорту — це вже покриває тест R14).

## Definition of Done

> Поки імпорт у польоті (парсинг або read-back), на `/item` не можна ні відкрити редактор, ні
> зберегти його; після панелі імпорту редактор не з'являється сам; нові тести червоніють на
> поточному коді; `make check` зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
