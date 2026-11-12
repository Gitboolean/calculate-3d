---
id: T6
title: "importing.service.parse_slicer_file: готовність налаштувань, розбір, підстановка зіставлень, помилки"
layer: "app"
deps: ["T4", "T5"]
acs: ["AC-01", "AC-02", "AC-04", "AC-07", "AC-09", "AC-11", "AC-12", "AC-13", "AC-14"]
files_hint: ["backend/src/calculate3d/modules/importing/service.py", "backend/src/calculate3d/modules/importing/schemas.py", "backend/tests/unit/test_importing_service.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T6 — importing.service.parse_slicer_file: готовність налаштувань, розбір, підстановка зіставлень, помилки

## Why

Потоки 1 і 4 [sad.md](../sad.md) §6; реєстр 9 кодів `importing.*` — deferral D1 у [api-sync-report.md](../contracts/api-sync-report.md). AC-04 (налаштування — так само, як `costing.settings_missing`), AC-07/AC-09 (`plastic_id: null` для незіставленого), AC-12…AC-14 у [PRD §5](../PRD.md).

## What

- `schemas.py`: `SlicerFile`, `SlicedPlate`, `SlicerFilament` (`usage_mg`, `plastic_id: str | None`), `FilamentMappingInput` (шаблон `^#[0-9A-F]{6}$`, назва 1–200), Problem-моделі `ImportRejectedProblem` (`Literal` кодів) і `ImportSettingsMissingProblem` — поля й межі дослівно з [openapi.yaml](../contracts/openapi.yaml).
- `service.py`: `AppError`-підкласи для `importing.settings_missing` (409, `missing`), `importing.file_too_large` (413), `not_slicer_project`, `not_sliced`, `multiple_sliced_plates`, `corrupted_file`, `print_time_out_of_range`, `no_filament_usage` (422) — повідомлення українською.
- `parse_slicer_file(conn, body: bytes) -> SlicerFile`: (1) готовність через `pricing.service` (AC-04) — до розбору; (2) `parser`; (3) `repo.find_mappings` → `plastic_id`. Нічого не пише.

## Definition of Done

> Юніт-тести service показують: без пластиків чи налаштувань — ImportSettingsMissing з переліком missing до розбору, кожен ParseError — свій AppError importing.* з українським повідомленням, а підставлений plastic_id береться лише з наявного зіставлення (інакше null).

- [ ] Юніт-тести: порожні пластики / налаштування → `ImportSettingsMissing` і парсер не викликано
- [ ] Кожен код парсера мапиться на свій `AppError` з HTTP-статусом контракту; тест, що кожне повідомлення модуля `importing` — українською ([sad.md](../sad.md) §10 «Локалізація»)
- [ ] Збережене зіставлення підставляє `plastic_id`; та сама назва з іншим кольором → `null` (AC-09)
- [ ] `make api-check` зелений; `test_module_boundaries` зелений (`importing → pricing` лише через `service.py`)

## Notes

Логування: тіло, вміст файлу й назви з нього не логуються ([sad.md](../sad.md) §8 Logging).
