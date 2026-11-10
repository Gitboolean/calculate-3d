# Tracker — print-file-import

> Status of every task in the epic. `implement-tasks` updates `done` as it commits each task.
> States: `todo` · `in_progress` · `blocked` · `review` · `done`. Оцінка: S = 2 год, M = пів дня, L = день.

| # | Task | Layer | Owner | Estimate | Blocked by | Status |
|---|---|---|---|---|---|---|
| [T1](./T1-promote-filament-mappings-migration.md) | Промоутнути staged-міграцію filament_mappings і дзеркало importing/tables.py | migration | Anton Pohorielov | S | — | done |
| [T2](./T2-slicer-fixtures-and-bad-file-generator.md) | Скопіювати еталонні файли слайсера у фікстури й написати генератор поганих файлів | tests | Anton Pohorielov | M | — | done |
| [T3](./T3-parser-archive-limits-and-plate-chain.md) | Парсер: межі читання архіву й ланцюжок «проєкт Bambu → нарізаний → одна пластина» | domain | Anton Pohorielov | M | T2 | done |
| [T4](./T4-parser-numbers-normalization-and-merge.md) | Парсер: числа, нормалізація філамента, злиття однакових пар і межі файлу | domain | Anton Pohorielov | L | T3 | done |
| [T5](./T5-importing-repo-and-remember-mappings.md) | importing.repo: пошук зіставлень за (назва, колір) і upsert; remember_mappings у service | infra | Anton Pohorielov | M | T1 | done |
| [T6](./T6-importing-service-parse-slicer-file.md) | importing.service.parse_slicer_file: готовність налаштувань, розбір, підстановка зіставлень, помилки | app | Anton Pohorielov | M | T4, T5 | done |
| [T7](./T7-request-guard-octet-stream-exception.md) | RequestGuard: приймати application/octet-stream лише для POST /api/importing/parse | wiring | Anton Pohorielov | S | — | done |
| [T8](./T8-importing-parse-router.md) | Роутер POST /api/importing/parse: потокове читання під межею 100 МБ, problem+json, api-types | ports | Anton Pohorielov | M | T6, T7 | done |
| [T9](./T9-catalog-save-item-with-mappings.md) | catalog: ItemInput.filament_mappings і remember_mappings у транзакції збереження виробу | app | Anton Pohorielov | M | T5 | done |
| [T10](./T10-importing-nfr-and-reference-tests.md) | NFR і еталонні тести імпорту: точність донату, латентність 100 МБ, збереженість, перенарізка | tests | Anton Pohorielov | M | T8, T9 | todo |
| [T11](./T11-shared-ui-dialog.md) | Додати shadcn-примітив dialog у shared/ui | ui | Anton Pohorielov | S | — | todo |
| [T12](./T12-slicer-import-compose-model.md) | features/slicer-import/model: compose.ts — рядки з точних мг, конфлікти сумування, diff «було → стало» | domain | Anton Pohorielov | M | T8 | todo |
| [T13](./T13-slicer-import-upload-and-rejections.md) | features/slicer-import: кнопка «Імпортувати файл», мутація розбору й повідомлення відмов | ui | Anton Pohorielov | M | T8 | todo |
| [T14](./T14-slicer-import-filament-mapping-panel.md) | features/slicer-import: список філаментів, вибір пластику, підтвердження сумування | ui | Anton Pohorielov | L | T11, T12, T13 | todo |
| [T15](./T15-calculate-page-import-and-save-mappings.md) | Сторінка розрахунку: імпорт у форму і передача зіставлень під час збереження виробу | ui | Anton Pohorielov | M | T9, T14 | todo |
| [T16](./T16-item-page-reslice-was-became.md) | Сторінка виробу: імпорт перенарізки з «було → стало», підтвердженням і скасуванням | ui | Anton Pohorielov | M | T15 | todo |
| [T17](./T17-docs-mg-suffix-and-contract-reconcile.md) | Документація: суфікс *_mg у CLAUDE.md, закриття D1/D3 у api-sync-report | docs | Anton Pohorielov | S | T10, T16 | todo |

**Total:** 17 tasks, ~8.5 person-days.
