---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-11-09"
feature_size: M
stage: "04-05"
ticket: ""
---

# 0002 — Upload the slicer file as a raw application/octet-stream body held in memory

- **Status:** Accepted
- **Date:** 2026-11-09
- **Deciders:** Anton Pohorielov (автор), architecture-design pass

## Context

ADR 0001 відправляє файл слайсера на сервер. Чинний `core/guard.py` (`RequestGuard`, cost-calculator ADR 0007) відповідає `415` на кожен змінний `/api`-запит із тілом не `application/json`. Це правило — один із шарів захисту від CSRF: «прості» CORS-типи (`text/plain`, `multipart/form-data`, `application/x-www-form-urlencoded`) чужа сторінка може надіслати без preflight. PRD §8 №2 питає, як прийняти файл, не послабивши цей захист (AC-15). Крім того, межі розміру тіла в застосунку немає, а NFR вимагає «0 байтів файлу на диску» і відмову для файлу понад 100 МБ (PRD §6).

## Decision drivers

- QG-3 Доступ лише автору / AC-15: сторонній сайт не може підсунути файл.
- QG-2 / PRD §6 «Файл не зберігається»: 0 байтів файлу на диску після імпорту, успішного чи відхиленого.
- PRD §6 «Межа розміру файлу ≤ 100 МБ» (тест 100 МБ + 1 байт) і QG-4 p95 ≤ 5 с.
- SAD §2: без нових runtime-залежностей; `python-multipart` не встановлено.

## Considered options

1. **Сире тіло `application/octet-stream`** — браузер надсилає байти файлу як тіло `POST`; `RequestGuard` дозволяє цей тип лише для маршруту імпорту; сервер читає потік у пам'ять під межею.
2. **`multipart/form-data` + `UploadFile`** — ідіоматичне завантаження FastAPI через нову залежність `python-multipart`.
3. **Base64 у JSON** — файл як текстове поле JSON; `RequestGuard` не змінюється.

## Decision outcome

**Chosen:** Option 1.

- **Guard.** `RequestGuard` отримує один явний виняток: `POST` на маршрут імпорту приймає **лише** `Content-Type: application/octet-stream`, а будь-який інший тип там — `415`. Усі інші змінні `/api`-запити, як і раніше, приймаються лише як `application/json`. Перевірки `Host`, `Origin` і `Sec-Fetch-Site` діють без змін. `application/octet-stream` не входить до «простих» CORS-типів, тож браузер стороннього сайту мусить спершу надіслати preflight, а той завжди невдалий, бо `CORSMiddleware` немає.
- **Межа розміру.** 100 МБ = **100 000 000 байт** (десяткові мегабайти — так розмір файлу показує Finder). `Content-Length` понад межу → `413` до читання тіла; без `Content-Length` (chunked) потік обривається на першому байті понад межу → `413`. Код помилки — `importing.file_too_large`; повідомлення українською називає межу (AC-13).
- **Пам'ять, а не диск.** Тіло збирається в `bytes` і відкривається через `zipfile.ZipFile(io.BytesIO(...))`. Тимчасових файлів, логування тіла чи кешу немає. Після відповіді байти звільняються.
- **Контракт.** Тіло описується в OpenAPI через `openapi_extra` (`application/octet-stream`, `format: binary`); веб передає `File`/`Blob` через `openapi-fetch` без JSON-серіалізації (`bodySerializer`).

## Consequences

**Positive**
- Захист від CSRF не слабшає: виняток вузький (один маршрут, один тип), і його не можна відправити без preflight.
- Файл ніколи не торкається диска; NFR «0 байтів» перевіряється інтеграційним тестом без налаштування spooling.
- Жодної нової залежності; найменше пам'яті й найшвидше з трьох варіантів (без +33 % base64 і без розбору гігантського JSON-рядка).

**Negative**
- Опис тіла в OpenAPI задається вручну (`openapi_extra`), а не виводиться з сигнатури; `api-types-check` ловить розходження, але не помилку в самому описі.
- `RequestGuard` тепер знає про один конкретний маршрут — це перший виняток у правилі «лише JSON» (поправка до cost-calculator ADR 0007 записується в §8 SAD).
- До 100 МБ на один запит у пам'яті процесу — прийнятно для одного автора та одного імпорту за раз (PRD §6 Throughput N/A).

**Neutral**
- Варіант 2 відкинуто через spooling Starlette (файли понад 1 МБ пишуться в тимчасовий файл на диску) і через те, що `multipart/form-data` — «простий» CORS-тип. Варіант 3 відкинуто через +33 % розміру і пам'ять для `QG-4`.

## Links

- PRD: [[../PRD.md]] AC-13, AC-15; §6 (межа розміру, «Файл не зберігається»), §6.1; §8 №2
- SAD: [[../sad.md]] §4, §8
- Related ADR: [[0001-parse-slicer-file-on-server-and-keep-only-numbers]]
- cost-calculator ADR: [[../../cost-calculator/adr/0007-guard-local-api-with-host-allowlist-and-same-origin-checks.md]]
