---
id: T7
title: "RequestGuard: приймати application/octet-stream лише для POST /api/importing/parse"
layer: "wiring"
deps: []
acs: ["AC-15"]
files_hint: ["backend/src/calculate3d/core/guard.py", "backend/tests/integration/test_request_guard.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T7 — RequestGuard: приймати application/octet-stream лише для POST /api/importing/parse

## Why

Поправка до cost-calculator ADR 0007 з [ADR 0002](../adr/0002-upload-slicer-file-as-raw-octet-stream-body-held-in-memory.md); [sad.md](../sad.md) §8 «Authentication / захист запитів», §6 «Cross-cutting», §11 ризик «виняток поширюється». AC-15 у [PRD §5](../PRD.md).

## What

- `core/guard.py`: точний виняток `(POST, "/api/importing/parse")` → дозволений лише `application/octet-stream`; решта змінних `/api` — як і раніше лише `application/json`. На маршруті імпорту `415` несе `detail` про `application/octet-stream` (контракт `OctetStreamRequired`).
- Відмова захисту не читає тіло.

## Definition of Done

> Інтеграційні тести захисту показують 415 для multipart/form-data і text/plain на маршруті імпорту та для octet-stream на будь-якому іншому змінному /api-маршруті, а перевірки Host/Origin/Sec-Fetch-Site діють на маршруті імпорту без змін.

- [ ] Нові параметризовані кейси в `test_request_guard.py`: маршрут імпорту × (`cross-site`, чужий `Origin`, чужий `Host`, `multipart/form-data`, `text/plain`) → 403 / 403 / 400 / 415 / 415
- [ ] `octet-stream` на `POST /api/catalog/items`, `PUT /api/catalog/items/{id}`, `POST /api/costing/quote` → 415 ([sad.md](../sad.md) §11)
- [ ] Наявні кейси етапу 1 зелені; `make api-check` зелений

## Notes

Маршруту ще немає (T8) — тести відмов захисту працюють і без нього, бо guard — middleware. Позитивний кейс «octet-stream з того самого origin проходить» додає T8.
