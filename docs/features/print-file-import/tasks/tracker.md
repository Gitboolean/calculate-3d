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
| [T10](./T10-importing-nfr-and-reference-tests.md) | NFR і еталонні тести імпорту: точність донату, латентність 100 МБ, збереженість, перенарізка | tests | Anton Pohorielov | M | T8, T9 | done |
| [T11](./T11-shared-ui-dialog.md) | Додати shadcn-примітив dialog у shared/ui | ui | Anton Pohorielov | S | — | cancelled (T14: alert-dialog covers AC-10, AC-05 is an inline panel) |
| [T12](./T12-slicer-import-compose-model.md) | features/slicer-import/model: compose.ts — рядки з точних мг, конфлікти сумування, diff «було → стало» | domain | Anton Pohorielov | M | T8 | done |
| [T13](./T13-slicer-import-upload-and-rejections.md) | features/slicer-import: кнопка «Імпортувати файл», мутація розбору й повідомлення відмов | ui | Anton Pohorielov | M | T8 | done |
| [T14](./T14-slicer-import-filament-mapping-panel.md) | features/slicer-import: список філаментів, вибір пластику, підтвердження сумування | ui | Anton Pohorielov | L | T11, T12, T13 | done |
| [T15](./T15-calculate-page-import-and-save-mappings.md) | Сторінка розрахунку: імпорт у форму і передача зіставлень під час збереження виробу | ui | Anton Pohorielov | M | T9, T14 | done |
| [T16](./T16-item-page-reslice-was-became.md) | Сторінка виробу: імпорт перенарізки з «було → стало», підтвердженням і скасуванням | ui | Anton Pohorielov | M | T15 | done |
| [T17](./T17-docs-mg-suffix-and-contract-reconcile.md) | Документація: суфікс *_mg у CLAUDE.md, закриття D1/D3 у api-sync-report | docs | Anton Pohorielov | S | T10, T16 | done |
| [T18](./T18-parser-never-500-on-malformed-input.md) | Парсер: будь-який пошкоджений вміст архіву → importing.corrupted_file, ніколи не 500 | app | Anton Pohorielov | S | T3, T4 | done |
| [T19](./T19-import-memory-within-sad-budget.md) | Пам'ять імпорту в бюджеті SAD §7: межа central directory до ZipFile і один буфер тіла | infra | Anton Pohorielov | M | T8, T18 | done |
| [T20](./T20-cancel-import-and-mapping-plastic-deleted.md) | Скасування імпорту в розрахунку і пояснення importing.plastic_not_found під час збереження | ui | Anton Pohorielov | M | T15, T16 | done |
| [T21](./T21-ui-tests-ac03-ac08-ac14-integer-rounding.md) | UI-тести AC-03/AC-08/AC-14 після імпорту і цілочислове округлення мг → сг | ui | Anton Pohorielov | M | T20 | done |
| [T22](./T22-client-side-file-size-check.md) | Кнопка імпорту: файл понад 100 МБ відхиляється в браузері без надсилання | ui | Anton Pohorielov | S | T13 | done |
| [T23](./T23-parser-real-cd-bound-and-ascii-digits.md) | Парсер: межа реального central directory, version > 6.3 і лише ASCII-цифри → importing.corrupted_file | app | Anton Pohorielov | M | T19 | done |
| [T24](./T24-plastic-not-found-invalidate-and-reslice-test.md) | plastic_not_found: інвалідувати пластики й довести скидання вибору на сторінці виробу | ui | Anton Pohorielov | S | T20 | done |
| [T25](./T25-calculate-import-round-key-and-cancel-restores-form.md) | Імпорт у розрахунку: key панелі за раундом імпорту і відновлення форми після скасування | ui | Anton Pohorielov | S | T20 | done |
| [T26](./T26-parser-cd-byte-cap-overlap-and-boundary-tests.md) | Парсер: межа байтів central directory, відмова на overlapped-записах і тести меж | app | Anton Pohorielov | M | T23 | todo |
| [T27](./T27-calculate-import-state-functional-updates.md) | Імпорт у розрахунку: один стан форми й імпорту з функціональними оновленнями | ui | Anton Pohorielov | S | T25 | todo |

**Total:** 27 tasks, ~8.5 person-days + ~2 person-days of review follow-ups (T18–T22, [review 2026-11-10](../_review/review-2026-11-10.md)) + ~1.5 person-days of re-review follow-ups (T23–T25, [review 2026-11-10 r2](../_review/review-2026-11-10-r2.md)) + ~1 person-day of r3 follow-ups (T26–T27, [review 2026-11-11 r3](../_review/review-2026-11-11-r3.md)).
