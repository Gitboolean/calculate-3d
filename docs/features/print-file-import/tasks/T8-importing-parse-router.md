---
id: T8
title: "Роутер POST /api/importing/parse: потокове читання під межею 100 МБ, problem+json, api-types"
layer: "ports"
deps: ["T6", "T7"]
acs: ["AC-01", "AC-02", "AC-04", "AC-12", "AC-13", "AC-14", "AC-15"]
files_hint: ["backend/src/calculate3d/modules/importing/router.py", "backend/src/calculate3d/main.py", "backend/tests/integration/test_importing_api.py", "backend/tests/integration/test_importing_bad_files.py", "backend/tests/integration/test_importing_no_disk.py", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T8 — Роутер POST /api/importing/parse: потокове читання під межею 100 МБ, problem+json, api-types

## Why

Операція `parseSlicerFile` у [openapi.yaml](../contracts/openapi.yaml); потік читання тіла — [ADR 0002](../adr/0002-upload-slicer-file-as-raw-octet-stream-body-held-in-memory.md); Critical flow 3 [sad.md](../sad.md) §6; deferral D3 у [api-sync-report.md](../contracts/api-sync-report.md). AC-01, AC-02, AC-04, AC-12…AC-15 у [PRD §5](../PRD.md).

## What

- `router.py`: `APIRouter(prefix="/api/importing")`, `POST /parse` читає `request.stream()` у `bytearray` і обриває на першому байті понад 100 000 000 → `importing.file_too_large` (413) без читання далі. Тіло — `openapi_extra` (`application/octet-stream`, `format: binary`), відповіді `409/413/415/422` — як у контракті. Router — лише HTTP; виклик `service.parse_slicer_file`.
- Підключити роутер у `create_app()` (`main.py`).
- Інтеграційні тести: еталони → тіло відповіді; `test_importing_bad_files.py` — `parametrize(BAD_FILES)`, кожен < 5 с і з очікуваним кодом; `test_importing_no_disk.py` — вміст `tempfile.gettempdir()` і каталогу БД до/після успішного й відхиленого імпорту ([sad.md](../sad.md) §10 QG-2); позитивний кейс guard для octet-stream з того самого origin.
- `make api-types` → закомітити оновлений `web/src/shared/api/schema.d.ts`.

## Definition of Done

> Інтеграційні тести показують, що parseSlicerFile повертає контрактний SlicerFile для обох нарізаних еталонів, 413 importing.file_too_large для 100 000 001 байт, очікуваний код для кожного випадку bad_files без 500, 0 нових файлів на диску, а make api-types-check зелений.

- [ ] `vtulka_A.gcode.3mf` → 200, `print_time_s: 5880`, один філамент 11 540 мг; з `make_filament_mapping` → `plastic_id` підставлено (AC-01)
- [ ] `LITTLE_TREES` → пластина `{index: 1, name: "mini christmas tree"}`, три філаменти (AC-02); без налаштувань → 409 `importing.settings_missing` з `missing` (AC-04)
- [ ] Кожен `BAD_FILES` → очікуваний код, жодного `internal_error`; 100 000 001 байт → 413 (AC-13); 0 байтів файлу на диску
- [ ] Тест OpenAPI: маршрут має `application/octet-stream` + `format: binary`, а `413/422` — під `application/problem+json` (D3); `make check` зелений

## Notes

Ділить `schema.d.ts` з T9 — `implement-tasks` серіалізує їх в одну смугу. Латентність p95 і файл рівно 100 000 000 байт — у T10.
