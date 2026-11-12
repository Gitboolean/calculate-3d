---
id: T2
title: "Скопіювати еталонні файли слайсера у фікстури й написати генератор поганих файлів"
layer: "tests"
deps: []
acs: ["AC-12", "AC-13"]
files_hint: ["backend/tests/fixtures/slicer/"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T2 — Скопіювати еталонні файли слайсера у фікстури й написати генератор поганих файлів

## Why

Парсер і всі інтеграційні тести імпорту спираються на ті самі еталони й набір поганих файлів ([sad.md](../sad.md) §10 QG-1, QG-2). Фікстури без production-коду можна писати паралельно з міграцією.

## What

- Скопіювати `docs/features/print-file-import/example-import/{vtulka_A.3mf, vtulka_A.gcode.3mf, LITTLE_TREES_-_multicolor.gcode.3mf}` у `backend/tests/fixtures/slicer/` + `__init__.py` з шляхами-константами.
- `backend/tests/fixtures/slicer/bad_files.py`: функції, що з еталона `vtulka_A.gcode.3mf` будують у пам'яті (`zipfile` у `BytesIO`) кожен випадок переліку [sad.md](../sad.md) §10 QG-2 — не ZIP, обрізаний ZIP, порожнє тіло, 10 001 запис, частина > 8 000 000 байт, заголовок, що бреше про розмір, ZIP-бомба G-code, billion laughs, XXE, CAD-3MF, позначка `OrcaSlicer`, дві нарізані пластини, дублікати назв, NaN / нескінченність / експонента / від'ємні грами, нульовий і завеликий час, жодного філамента з витратою > 0, завелика назва, неканонічний колір, > 32 пари, `usage_mg` > 2^53−1.
- Кожен випадок — `BadFile(name, body: bytes, expected_code: str)`; таблиця `BAD_FILES` для `pytest.mark.parametrize`. Коди — ті, що в [openapi.yaml](../contracts/openapi.yaml) `ImportRejectedProblem` / `FileTooLarge`.

## Definition of Done

> backend/tests/fixtures/slicer/ містить три еталони, а bad_files.py будує в пам'яті кожен випадок переліку SAD §10 QG-2 з очікуваним кодом importing.* і самоперевіркою, що кожен випадок генерується.

- [ ] Три еталони лежать у `backend/tests/fixtures/slicer/` (у репо — лише вони, жодного згенерованого файлу)
- [ ] Юніт-тест самоперевірки: кожен елемент `BAD_FILES` генерується, має непорожній `expected_code` з набору коду контракту, і випадок «ZIP-бомба» < 1 МБ стиснутого розміру
- [ ] `ruff` + `mypy --strict` зелені (фікстури теж під mypy)

## Notes

Файл 100 МБ для NFR-тесту тут **не** генерується — його будує T10 у самому тесті. Генератор не залежить від `parser.py`: він знає лише формат файлу (SAD §8).
