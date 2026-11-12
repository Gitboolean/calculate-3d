---
id: T22
title: "Кнопка імпорту: файл понад 100 МБ відхиляється в браузері без надсилання"
layer: "ui"
deps: ["T13"]
acs: ["AC-13"]
files_hint: ["web/src/features/slicer-import/ui/ImportFileButton.tsx", "web/src/features/slicer-import/ui/ImportFileButton.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T22 — Кнопка імпорту: файл понад 100 МБ відхиляється в браузері без надсилання

## Why

Review Q3: межу 100 МБ перевіряє лише сервер після надсилання; коли 413 приходить до читання тіла, браузер може побачити розрив з'єднання → загальний FALLBACK замість «Файл більший за 100 МБ» (AC-13 «називає причину простими словами»). Джерело: [review 2026-11-10](../_review/review-2026-11-10.md).

## What

- `ImportFileButton.tsx:25`: перед `parse.mutate` перевірити `file.size > 100_000_000` → показати текст `importing.file_too_large`, нічого не надсилати; серверний 413 лишається справжньою перевіркою.

## Definition of Done

> Тест ImportFileButton з File розміром понад 100 МБ показує «Файл більший за 100 МБ» і не викликає fetch, а make web-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений
