---
id: T3
title: "Парсер: межі читання архіву й ланцюжок «проєкт Bambu → нарізаний → одна пластина»"
layer: "domain"
deps: ["T2"]
acs: ["AC-02", "AC-12", "AC-13"]
files_hint: ["backend/src/calculate3d/modules/importing/parser.py", "backend/tests/unit/test_importing_parser.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T3 — Парсер: межі читання архіву й ланцюжок «проєкт Bambu → нарізаний → одна пластина»

## Why

Кроки 0–3 ланцюжка перевірок і межі читання архіву ([sad.md](../sad.md) §8 «Межі читання архіву», «Джерело чисел і ланцюжок перевірок»; [ADR 0001](../adr/0001-parse-slicer-file-on-server-and-keep-only-numbers.md)). Порядок перевірок — AC-12; відмови — AC-13; пропуск ненарізаних пластин — AC-02 ([PRD §5](../PRD.md)).

## What

- `modules/importing/parser.py` — чиста функція `bytes →` проміжна структура пластини | `ParseError(code)` (без I/O, як `costing/domain.py`), лише stdlib (`zipfile`, `xml.etree.ElementTree`, `json`; [sad.md](../sad.md) §2).
- Крок 0: відкриття ZIP; ≤ 10 000 записів; читаються лише 4 частини за точною назвою; кожна ≤ 8 000 000 байт і за заголовком, і фактичним `read(limit + 1)`; шифрування / невідомий метод / дублікати назв → `corrupted_file`. G-code і `Auxiliaries/` не розпаковуються ніколи.
- Крок 1: `Application` з префіксом `BambuStudio-` + наявний `project_settings.config`, інакше `not_slicer_project`. Крок 2: є пластина з `gcode_file` і результатами в `slice_info.config`, інакше `not_sliced`. Крок 3: понад одна нарізана → `multiple_sliced_plates`; результат — номер і назва єдиної нарізаної пластини.

## Definition of Done

> Юніт-тести парсера показують: не-ZIP і CAD-3MF/OrcaSlicer → not_slicer_project, vtulka_A.3mf → not_sliced, дві нарізані пластини → multiple_sliced_plates, кожне порушення меж архіву → corrupted_file, а LITTLE_TREES дає пластину 1 «mini christmas tree».

- [ ] Юніт-тести на еталонах: `vtulka_A.gcode.3mf` → пластина 1; `LITTLE_TREES` → пластина 1 «mini christmas tree»; `vtulka_A.3mf` → `not_sliced`
- [ ] Юніт-тести на випадках T2 для кроків 0–3 дають очікуваний код; billion laughs і XXE не розгортаються (закріплює Expat 2.8.1, [sad.md](../sad.md) §2)
- [ ] Жоден тест не пише на диск; `make api-check` зелений

## Notes

Ділить `parser.py` з T4 — одна смуга. Коди тут — рядки-константи парсера; `AppError`-підкласи з'являються в T6. Межі безпеки (крок 0) мають пріоритет над порядком AC-12 ([sad.md](../sad.md) §8).
