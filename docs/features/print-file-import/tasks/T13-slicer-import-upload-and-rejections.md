---
id: T13
title: "features/slicer-import: кнопка «Імпортувати файл», мутація розбору й повідомлення відмов"
layer: "ui"
deps: ["T8"]
acs: ["AC-04", "AC-12", "AC-13", "AC-14", "AC-15"]
files_hint: ["web/src/features/slicer-import/api/", "web/src/features/slicer-import/ui/ImportFileButton.tsx", "web/src/features/slicer-import/ui/ImportRejection.tsx", "web/src/features/slicer-import/ui/*.test.tsx"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T13 — features/slicer-import: кнопка «Імпортувати файл», мутація розбору й повідомлення відмов

## Why

Слайс `features/slicer-import` з [sad.md](../sad.md) §4 «UI-architecture» і §5; тіло-`File` — [ADR 0002](../adr/0002-upload-slicer-file-as-raw-octet-stream-body-held-in-memory.md); Critical flow 3 і Flow 4 [sad.md](../sad.md) §6. AC-04, AC-12…AC-14 у [PRD §5](../PRD.md).

## What

- `api/parse.ts`: `useParseSlicerFile()` — TanStack `useMutation` через типізований `openapi-fetch` (`body: File`, `bodySerializer` без JSON, `Content-Type: application/octet-stream`).
- `ui/ImportFileButton.tsx`: `Button` + прихований `<input type=file accept=".3mf">`, стан завантаження; результат — колбек `onParsed(SlicerFile)`.
- `ui/ImportRejection.tsx`: мапа код → українське пояснення (не нарізаний — «наріжте пластину й завантажте нарізаний файл»; кілька пластин; не проєкт Bambu Studio; пошкоджений; завеликий; час поза межами; без витрати) + «Ввести вручну»; `importing.settings_missing` — перелік `missing` і посилання на `/settings`.

## Definition of Done

> Vitest-тести показують, що вибір файлу надсилає його сирим тілом application/octet-stream, а кожен код importing.* і 409 settings_missing дає своє українське пояснення з пропозицією ввести дані вручну (і посиланням на налаштування для AC-04).

- [ ] Тест мутації (`msw` / мок `fetch`, як у наявних тестах): тіло — той самий `File`, `Content-Type: application/octet-stream`
- [ ] Параметризований тест `ImportRejection`: кожен код контракту має непорожнє українське повідомлення й дію «Ввести вручну»; невідомий код → загальне повідомлення, не падіння
- [ ] `make web-check` зелений

## Notes

`MissingSettings` живе в `features/quote-form` — імпортувати звідти не можна (FSD). Якщо потрібен той самий вигляд — підняти компонент у `entities/price-settings/ui` окремим коміт-кроком у цій задачі. Назви з файлу — лише текст, без `dangerouslySetInnerHTML` ([sad.md](../sad.md) §8 Output encoding).
