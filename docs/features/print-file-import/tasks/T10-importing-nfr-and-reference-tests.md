---
id: T10
title: "NFR і еталонні тести імпорту: точність донату, латентність 100 МБ, збереженість, перенарізка"
layer: "tests"
deps: ["T8", "T9"]
acs: ["AC-01", "AC-02", "AC-05", "AC-11", "AC-13"]
files_hint: ["backend/tests/integration/test_importing_reference_files.py", "backend/tests/integration/test_nfr_import_latency.py", "backend/tests/integration/test_importing_durability.py", "backend/tests/integration/test_importing_item_reslice.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T10 — NFR і еталонні тести імпорту: точність донату, латентність 100 МБ, збереженість, перенарізка

## Why

Сценарії [sad.md](../sad.md) §10 QG-1, QG-4, «Збереженість зіставлень»; числа — з [PRD §5](../PRD.md) AC-01, AC-02, AC-05, AC-11 і §6 NFR.

## What

- `test_importing_reference_files.py` — таблиця «еталон → розбір → `quoteCost`»: `vtulka_A` 1 154 сг, 5 880 с → 18,82 ₴ і розбивка 4,62 / 1,06 / 11,43 / 1,71 ₴ (AC-01); ціна 650 ₴/кг → 22,00 ₴ (AC-11).
- `test_importing_item_reslice.py` — виріб «Підставка» → `updateItem` з рядками імпорту → 60,73 ₴, назва без змін (AC-05).
- `test_nfr_import_latency.py` — 20 прогонів на кожен файл, p95 відповіді сервера ≤ 5 с; файл рівно 100 000 000 байт (еталон + незжате вкладення, генерується в тесті).
- `test_importing_durability.py` — зберегти виріб зі зіставленням → новий `create_app()` на тому самому файлі БД → імпорт підставляє той самий пластик; видалити пластик → `plastic_id: null` (AC-11).

## Definition of Done

> Інтеграційні тести показують донат 18,82 ₴ для vtulka_A і 22,00 ₴ після зміни ціни, 60,73 ₴ після перенарізки «Підставки», p95 ≤ 5 с для еталонів і файлу рівно 100 000 000 байт, а зіставлення переживає перезапуск застосунку й забувається після видалення пластику.

- [ ] Усі чотири файли зелені; числа збігаються з PRD до копійки
- [ ] Латентність вимірюється на тій самій машині, що й `test_nfr_latency.py` етапу 1
- [ ] `make api-check` зелений, тест 100 МБ не пише файл на диск

## Notes

Ці тести складають рядки так само, як веб (сума мг → `ceil(/10)` сг), — це другий бік accepted debt [sad.md](../sad.md) §11: розходження з `compose.ts` (T12) ловлять однакові приклади.
