---
id: T4
title: "Парсер: числа, нормалізація філамента, злиття однакових пар і межі файлу"
layer: "domain"
deps: ["T3"]
acs: ["AC-02", "AC-03", "AC-09", "AC-10", "AC-13", "AC-14"]
files_hint: ["backend/src/calculate3d/modules/importing/parser.py", "backend/tests/unit/test_importing_parser.py"]
owner: "Anton Pohorielov"
estimate: "L"
status: "todo"
---

# T4 — Парсер: числа, нормалізація філамента, злиття однакових пар і межі файлу

## Why

Кроки 4–5 ланцюжка й нормалізація ([sad.md](../sad.md) §8 «Джерело чисел…», «Нормалізація філамента»; [ADR 0004](../adr/0004-compose-quote-rows-in-the-web-from-exact-milligrams.md) — точні `usage_mg`). AC-02, AC-03 (час вгору до хвилини), AC-09 (ключ назва + колір), AC-10 (виняток однакових котушок), AC-13/AC-14 у [PRD §5](../PRD.md).

## What

- Крок 4 (цілісність): `prediction` і кожен `<filament id type color used_g>` наявні; `id` має назву в `filament_settings_id[id-1]`; інакше `corrupted_file`.
- Числа — через `Decimal` з рядка: NaN, нескінченність, експонента, від'ємні, > 3 знаків після коми, `usage_mg` > 2^53−1 → `corrupted_file`. Час — `ceil(prediction / 60) × 60`.
- Нормалізація: колір → `#RRGGBB` верхнім регістром (альфа відкидається, інша форма → `corrupted_file`); назва — лише `strip()`, з урахуванням регістру, без NFC; 1–200 code points.
- Філаменти без запису в `slice_info` або з `used_g = 0` пропускаються; однакові пари (назва, колір) зливаються з точною сумою мг; > 32 пари → `corrupted_file`. Крок 5: час > 0 і ≤ 360 000 000 с → інакше `print_time_out_of_range`; жодного філамента > 0 → `no_filament_usage`.

## Definition of Done

> Юніт-тести парсера дають для vtulka_A 11 540 мг і 5 880 с, для LITTLE_TREES 15 490 / 2 230 / 2 360 мг і 5 460 с без коричневого, і очікувані коди для кожного числового поганого випадку T2.

- [ ] Еталони: `vtulka_A.gcode.3mf` → `Bambu PLA Basic @BBL A1M`, `#FFFFFF`, 11 540 мг, 5 880 с (5 828 с вгору); `LITTLE_TREES` → 15 490 / 2 230 / 2 360 мг, 5 460 с (5 401 с вгору), `#6F5034` відсутній (AC-02)
- [ ] Приклади AC-03: 5 820 с лишається 5 820; `11.543` → 11 543 мг. AC-09: `#ffffff`, `#FFFFFFFF` → `#FFFFFF`; назва з пробілами на краях обрізана, регістр збережено
- [ ] Злиття двох однакових слотів дає один філамент із сумою мг (AC-10, виняток); 33 різні пари → `corrupted_file`
- [ ] Кожен числовий випадок T2 дає очікуваний код; `make api-check` зелений

## Notes

Межу 1 000 000 г на пластик **не** перевіряє парсер — її ловить `costing` після сумування у вебі (AC-14, [ADR 0004](../adr/0004-compose-quote-rows-in-the-web-from-exact-milligrams.md)). Якщо задача виходить за ~500 LOC разом із тестами — винести нормалізацію в `importing/normalize.py`.
