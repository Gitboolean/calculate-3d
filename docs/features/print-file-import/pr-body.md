## Summary

Етап 2 калькулятора: імпорт нарізаного файлу Bambu Studio (`.3mf`) у розрахунок або в
наявний виріб. Сервер розбирає файл у пам'яті й повертає витрату кожного філаменту та час
друку, а сам файл відкидає. Веб зіставляє філаменти з пластиками й рахує мінімальний донат
за поточними цінами. Зіставлення запам'ятовуються разом зі збереженим виробом, а виріб
змінюється лише після підтвердження «було → стало». Погані файли відхиляються з поясненням
замість нулів. Контекст і цілі: [PRD](docs/features/print-file-import/PRD.md).

## Acceptance criteria

- AC-01: «vtulka_A» → PLA білий 11,54 г, 1 год 38 хв, донат 18,82 ₴ (4,62 / 1,06 / 11,43 / 1,71), файл не зберігається ✓
- AC-02: «LITTLE_TREES» → пластина 1 «mini christmas tree», 15,49 / 2,23 / 2,36 г, 1 год 31 хв, невикористаний коричневий пропущено ✓
- AC-03: час і грами округлюються лише вгору, сума філаментів одного пластику округлюється один раз (2,001 + 2,001 → 4,01 г) ✓
- AC-04: без пластиків або налаштувань цін імпорт блокується 409 з переліком того, чого бракує ✓
- AC-05: «було → стало» перед збереженням, ручне виправлення до підтвердження, назва виробу не змінюється ✓
- AC-06: скасування або відхилення залишає виріб без змін, часткових змін не буває ✓
- AC-07: незіставлений філамент показано як у слайсері, зіставлення запам'ятовується лише при збереженні виробу ✓
- AC-08: заміна підставленого пластику перезаписує зіставлення й не чіпає інших виробів ✓
- AC-09 / AC-09b: без пластику для кожного філаменту немає ні донату, ні збереження; якщо пластику ще немає, інструмент веде в налаштування ✓
- AC-10: два різні філаменти → один пластик: інструмент питає перед сумуванням; однакові назва + колір сумуються одразу ✓
- AC-11: нова ціна пластику застосовується одразу (22,00 ₴); видалення пластику забуває зіставлення ✓
- AC-12: ненарізаний проєкт → `importing.not_sliced`, порядок перевірок дотримано ✓
- AC-13: кілька нарізаних пластин, файл не з Bambu, пошкоджений файл або файл > 100 МБ відхиляються з причиною ✓
- AC-14: межі часу й витрати з файлу відхиляються, межі пластиків (32 рядки, 1 000 000 г) — як при ручному введенні ✓
- AC-15: сторонній сайт (Origin), чужий `Host` і `octet-stream` поза `/api/importing/parse` відхиляються ✓

## Design

- PRD: `docs/features/print-file-import/PRD.md`
- Architecture: `docs/features/print-file-import/sad.md`
- Decisions: `docs/features/print-file-import/adr/` (0001–0005)
- Data model + migration: `docs/features/print-file-import/data-model.md` (Alembic `20261110_2110_create_filament_mappings`)
- API: `docs/features/print-file-import/contracts/openapi.yaml` (`api-sync-report.md`: PASS (with deferrals))
- Test plan: `docs/features/print-file-import/test-plan.md`
- Reviews: `docs/features/print-file-import/_review/`, 9 раундів, останній `review-2026-11-11-r9.md`: **PASS**
- Changelog: `docs/features/print-file-import/CHANGELOG.md`

## Tasks (SDLC-Task trailers)

<details><summary>33 task commits (з 67 комітів гілки; T11 скасовано — alert-dialog покрив потребу)</summary>

- `c87241f` feat(print-file-import): promote filament_mappings migration and importing tables — T1
- `14d5b14` test(print-file-import): slicer reference fixtures and in-memory bad-file generator — T2
- `0a89b07` feat(print-file-import): parser archive read limits and sliced-plate chain — T3
- `af0747b` feat(print-file-import): parser numbers, filament normalization and slot merge — T4
- `0b1170a` feat(print-file-import): importing repo lookup/upsert and remember_mappings — T5
- `9c246bf` feat(print-file-import): importing.service.parse_slicer_file and the importing error registry — T6
- `b021f10` feat(print-file-import): request guard takes octet-stream only on POST /api/importing/parse — T7
- `55f15f2` feat(print-file-import): POST /api/importing/parse router with a 100 MB streamed body — T8
- `115244f` feat(print-file-import): save filament mappings in the item-save transaction — T9
- `d63b593` test(print-file-import): reference, reslice, durability and latency NFR tests for import — T10
- `aa640aa` feat(print-file-import): slicer-import compose model and «було → стало» diff — T12
- `83c9c75` feat(print-file-import): import-file button, raw-body parse mutation and rejection messages — T13
- `bae855b` feat(print-file-import): filament mapping panel and merge confirmation — T14
- `3e70e23` feat(print-file-import): import a slicer file into the calculation and save its mappings — T15
- `7084af9` feat(print-file-import): re-slice an item with «було → стало», confirm or cancel — T16
- `71145cc` docs(print-file-import): *_mg suffix in CLAUDE.md, close D1/D3 in api-sync-report — T17
- `fb670ca` fix(print-file-import): parser never answers 500 on malformed archive content — T18
- `c1f58b2` fix(print-file-import): bound import memory — EOCD pre-check and one body buffer — T19
- `a2cdc27` fix(print-file-import): cancel an import and explain a deleted mapped plastic — T20
- `5abe086` fix(print-file-import): explain an over-limit imported usage; UI tests for AC-03/08/14 — T21
- `6eb8b49` fix(print-file-import): reject a file over 100 MB in the browser without uploading it — T22
- `7479ad0` fix(print-file-import): bound the central directory zipfile actually parses — T23
- `3447ff0` fix(print-file-import): refresh the plastic list after a deleted mapped plastic — T24
- `42467b4` fix(print-file-import): a re-import asks about merges again; cancel restores the form — T25
- `f9fec19` fix(print-file-import): cap the central directory bytes and reject overlapped entries — T26
- `8d9d025` fix(print-file-import): import, cancel and save errors update the current calculate state — T27
- `303118a` fix(print-file-import): cancel is locked while a save is in flight; reslice errors update the current import — T28
- `8b90221` test(print-file-import): pin the central directory byte cap and sync the SAD archive limits — T29
- `c90ee7c` fix(print-file-import): a rejected mapping resolves against what was sent; import is locked while saving — T30
- `21a8ad4` fix(print-file-import): saving is locked while a file is parsing — T31
- `81a1ef4` fix(print-file-import): the item editor's save is locked while a file is parsing — T32
- `4517b79` fix(print-file-import): «Змінити» on /item is locked while a file is importing — T33
- `a6ae2e9` test(print-file-import): a body of exactly 100 MB reaches the parser on CI — T34

</details>

## Verification

- Unit + integration (backend): `pytest` — 682 passed, 4 skipped (відомі пропуски безіменних схем у `test_contract.py`). Інтеграційні тести ганяють `TestClient` проти справжньої тимчасової SQLite після міграцій Alembic.
- Web: `vitest` — 367 passed (26 файлів); `vite build` ok.
- Lint + types: `ruff check` / `ruff format --check` (103 файли), `mypy --strict src` (44 файли), ESLint + Prettier + Steiger, `tsc -b` — чисто; `make api-types-check` — `schema.d.ts` синхронний з OpenAPI. Разом `make check` → exit 0 (2026-11-11).
- Ran the feature: `uv run calculate3d` (UI + API з одного процесу, як `make run`) на `127.0.0.1` з окремою тимчасовою БД (робоча `backend/var/` не зачіпалася). Міграція up → down → up вручну. Живий HTTP-сценарій на трьох еталонних файлах — 16/16 перевірок пройшли, у лозі сервера немає жодного 5xx і трейсбека: AC-04 (409 `settings_missing` з `[plastics, price_settings]`), AC-01/03 (11 540 mg → 1154 cg, 5880 s, донат 1882 коп із розбивкою 462/106/1143/171), AC-07 (без зіставлення → після збереження виробу підставляється), AC-11 (ціна 650 ₴/кг → 2200 коп; видалення пластику → зіставлення забуте), AC-05/08 (PUT перенарізки, каталог показує новий донат, зіставлення переписано), AC-06 (422 `plastic_not_found`, виріб байт-у-байт без змін), AC-02 (пластина 1 «mini christmas tree», 15 490/2 230/2 360 mg, 5460 s), AC-12 (`not_sliced`), AC-13 (`corrupted_file`, 413 `file_too_large`), AC-15 (403 Origin, 400 Host, 415 octet-stream на `/api/catalog/items`), UI віддається на `/`.
- Deferred: UI-потоки, які існують лише у вебі (панель зіставлення, підтвердження сумування AC-10, блокування донату AC-09/AC-14, «було → стало» AC-05 з 80,63 → 60,73 ₴), вручну в браузері не прокликувалися. Їх покривають vitest-тести сторінок і `test_importing_item_reslice.py`. За бажання — `/sdlc:verify-ui print-file-import`.

## Operational notes

- Migration: `20261110_2110_create_filament_mappings` (`f6268165ee91` ← `65f15a51514f`) створює `filament_mappings`. `make run` застосовує її сам. Rollback: `make migrate-down` один раз (видаляє лише запам'ятані зіставлення) + revert. Перед цим — копія `backend/var/calculate3d.db`.
- Feature flag / config: немає. Тіло імпорту ≤ 100 000 000 байт тримається в пам'яті (≈ 132 МБ піку, SAD §7).
- Known follow-ups: PRD §8 Q4, Q5 (due 2026-11-24); OrcaSlicer — поза обсягом етапу.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
