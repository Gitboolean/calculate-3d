---
id: T5
title: "Реалізувати чисту формулу собівартості costing.domain на Decimal з еталонною таблицею"
layer: "domain"
deps: []
acs: ["AC-04", "AC-06", "AC-06b", "AC-08", "AC-08b", "AC-13"]
files_hint: ["backend/src/calculate3d/core/money.py", "backend/src/calculate3d/modules/costing/__init__.py", "backend/src/calculate3d/modules/costing/domain.py", "backend/tests/unit/test_costing_domain.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T5 — Реалізувати чисту формулу собівартості costing.domain на Decimal з еталонною таблицею

## Why

[ADR-0002](../adr/0002-compute-cost-on-server-only.md) (формула в одному місці, лише на сервері), [ADR-0004](../adr/0004-exchange-quantities-as-scaled-integers.md) (масштабовані цілі), [sad.md](../sad.md) §10 QG-1 і §11 ризик «правила округлення застосовано не там». Критерії: AC-04, AC-06, AC-06b, AC-08, AC-08b, AC-13 у [PRD §5](../PRD.md).

## What

- `costing/domain.py`: frozen-dataclass входу (рядки пластику `price_per_kg_kop` × `usage_cg`, `print_time_s`, 6 полів налаштувань) → `Quote(min_donation_kop, breakdown{plastic,electricity,wear,scrap}_kop)`.
- Точна сума в `Decimal`; мінімальний донат — `ROUND_CEILING` з точної суми; рядки розбивки — `ROUND_HALF_UP` до копійки; брак = відсоток від суми пластик+електрика+знос.
- `core/money.py`: `wear_per_hour(printer_price_kop, printer_lifetime_h, parts_per_hour_kop) -> Decimal` (точне) + `round_half_up_kop()`; цю функцію використовують і `costing.domain`, і `pricing.service` (для `wear_per_hour_kop` у відповіді налаштувань, AC-04: 7,00 ₴), бо `pricing` не може імпортувати `costing` (ADR-0005).

## Definition of Done

- [ ] Еталонна таблиця ≥ 10 рядків: AC-06 (115,25 / 78,00 / 2,27 / 24,50 / 10,48), AC-06b (80,63; пластик 58,00), AC-08b (96,74 / 65,00 / 1,94 / 21,00 / 8,79), AC-13 (135,05), AC-04 знос 700 коп/год, нульовий тариф, брак 0 % і 100 %.
- [ ] Детермінований прогін (фіксований seed, ≥ 1 000 входів): `min_donation_kop ≥ точна сума` і `< точна сума + 1`.
- [ ] Жодного `float` у модулі; `mypy --strict` і `ruff` чисті.

## Notes

- **Blocked by:** —.
- Без I/O і без FastAPI — паралельна гілка з першого дня. Брак рахується від суми трьох складових; це звірено з AC-06: (78 + 2,268 + 24,5) × 0,1 = 10,4768.
