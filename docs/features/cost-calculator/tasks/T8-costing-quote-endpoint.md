---
id: T8
title: "Реалізувати costing.service.quote() і POST /api/costing/quote"
layer: "ports"
deps: ["T5", "T7"]
acs: ["AC-06", "AC-06b", "AC-07", "AC-08", "AC-09"]
files_hint: ["backend/src/calculate3d/modules/costing/service.py", "backend/src/calculate3d/modules/costing/schemas.py", "backend/src/calculate3d/modules/costing/router.py", "backend/src/calculate3d/main.py", "backend/tests/unit/test_costing_service.py", "backend/tests/integration/test_costing_api.py", "web/src/shared/api/schema.d.ts"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T8 — Реалізувати costing.service.quote() і POST /api/costing/quote

## Why

[sad.md](../sad.md) §6 «Critical flow 1: живий перерахунок»; [ADR-0002](../adr/0002-compute-cost-on-server-only.md); операція `quoteCost` у [openapi.yaml](../contracts/openapi.yaml). Критерії: AC-06, AC-06b, AC-07, AC-08, AC-09 у [PRD §5](../PRD.md).

## What

- `service.py`: `quote(input)` бере пластики й налаштування з `pricing.service` → `costing.domain`. Немає налаштувань або жодного пластику → `costing.settings_missing` (409, `missing=[…]`); невідомий `plastic_id` → `costing.plastic_not_found` (422). Пакетний варіант `quote_many(inputs)` для каталогу (ADR-0003): одне читання цін на всі вироби.
- `schemas.py`: `QuoteInput` (`plastics` minItems 1, `usage_cg ≥ 1`, `print_time_s ≥ 60` і кратний 60, повтор `plastic_id` → `model_validator` → 422), `Quote`, `CostBreakdown`.
- `router.py` `POST /api/costing/quote` з `responses=` з контракту; підключити; `make api-types`.

## Definition of Done

- [ ] Інтеграційні тести: AC-06, AC-06b, AC-08b (точні копійки донату й рядків), AC-07 (порожній список, `usage_cg: 0`, повтор пластику, `print_time_s: 0` / 90) → 422, AC-09 (без налаштувань / без пластиків) → 409 з `missing`.
- [ ] Unit-тести сервісу з підміненим `pricing.service`; `quote_many` робить фіксовану кількість звернень до `pricing`.
- [ ] `make check` зелений.

## Notes

- **Blocked by:** [T5](./T5-costing-domain-formula.md), [T7](./T7-pricing-router.md).
- `costing` нічого не зберігає (ADR-0005) — `repo.py`/`tables.py` немає. Напрямок залежностей лише `costing → pricing`.
